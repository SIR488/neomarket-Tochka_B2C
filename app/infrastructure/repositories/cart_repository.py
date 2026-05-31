from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload, joinedload

from app.infrastructure.models import Cart, CartItem, SKU

class CartRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def resolve_cart(
        self,
        customer_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
    ) -> Cart:
        query = (
            select(Cart)
            .where(
                or_(
                    Cart.customer_id == customer_id if customer_id else False,
                    Cart.session_id == session_id if session_id else False,
                )
            )
        )
        result = await self.session.execute(query)
        cart = result.scalar_one_or_none()

        if not cart:
            cart = Cart(customer_id=customer_id, session_id=session_id)
            self.session.add(cart)
            await self.session.commit()
            await self.session.refresh(cart)

        return cart


    async def get_by_id(self, cart_id: UUID) -> Optional[Cart]:
        query = (select(Cart)
                    .where(Cart.id == cart_id)
                    .options(selectinload(Cart.cart_items).selectinload(CartItem.sku).selectinload(SKU.stock)))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_cart_with_items(self, cart_id: UUID) -> Optional[Cart]:
        query = (select(Cart)
                    .where(Cart.id == cart_id)
                    .options(
                        joinedload(Cart.cart_items)
                        .joinedload(CartItem.sku)
                        .joinedload(SKU.stock))
                    )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_item(self, cart_id: UUID, sku_id: UUID) -> Optional[CartItem]:
        query = select(CartItem).where(CartItem.cart_id == cart_id, CartItem.sku_id == sku_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def add_or_update_item(self, cart_id: UUID, sku_id: UUID, quantity: int, unit_price_at_add: int):
        await self.session.flush()

        item = await self.get_item(cart_id, sku_id)
        if item:
            item.quantity += quantity
        else:
            item = CartItem(
                cart_id=cart_id,
                sku_id=sku_id,
                quantity=quantity,
                unit_price_at_add=unit_price_at_add
            )
            self.session.add(item)

        await self.session.commit()

    async def update_item_quantity(self, cart_id: UUID, sku_id: UUID, quantity: int) -> Optional[CartItem]:
        item = await self.get_item(cart_id, sku_id)
        if item:
            item.quantity = quantity

        await self.session.commit()
        return item

    async def remove_item(self, cart_id: UUID, sku_id: UUID):
        item = await self.get_item(cart_id, sku_id)
        if item:
            await self.session.delete(item)
            await self.session.commit()
            return item.id
        else:
            return None

    async def clear_cart(self, cart_id: UUID) -> None:
        """Очистить корзину (удалить все CartItem)"""
        query = delete(CartItem).where(CartItem.cart_id == cart_id)
        await self.session.execute(query)
        await self.session.commit()

    async def get_user_cart(self, customer_id: UUID) -> Optional[Cart]:
        """Получить корзину пользователя"""
        query = (select(Cart)
                 .where(Cart.customer_id == customer_id).
                 options(selectinload(Cart.cart_items)))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_guest_cart(self, session_id: UUID) -> Optional[Cart]:
        """Получить гостевую корзину"""
        query = (select(Cart)
                 .where(Cart.session_id == session_id)
                 .options(selectinload(Cart.cart_items)))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def merge_guest_into_user(
            self, customer_id: UUID, session_id: UUID
    ) -> Cart:
        """
        Сливает гостевую корзину в пользовательскую по правилу max(quantity).
        Возвращает user_cart.
        """
        user_cart = await self.get_user_cart(customer_id)
        guest_cart = await self.get_guest_cart(session_id)

        if not guest_cart or not guest_cart.cart_items:
            return user_cart or Cart(customer_id=customer_id)

        if not user_cart:
            user_cart = Cart(customer_id=customer_id)
            self.session.add(user_cart)

        guest_items_map = {item.sku_id: item for item in guest_cart.cart_items}

        for user_item in user_cart.cart_items:
            if user_item.sku_id in guest_items_map:
                guest_item = guest_items_map.pop(user_item.sku_id)
                user_item.quantity = max(user_item.quantity, guest_item.quantity)
                if user_item.unit_price_at_add is None:
                    user_item.unit_price_at_add = guest_item.unit_price_at_add

        for guest_item in guest_items_map.values():
            new_item = CartItem(
                cart_id=user_cart.id,
                sku_id=guest_item.sku_id,
                quantity=guest_item.quantity,
                unit_price_at_add=guest_item.unit_price_at_add,
            )
            self.session.add(new_item)

        await self.session.delete(guest_cart)

        return user_cart