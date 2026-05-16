from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import Optional
from uuid import UUID

from app.infrastructure.models import Cart, CartItem, SKU
from app.infrastructure.database import get_db
from app.api.v1.dependencies.customer_depends import get_current_customer_id_optional

async def resolve_cart(
    customer_id: Optional[UUID] = Depends(get_current_customer_id_optional),
    session_id: Optional[UUID] = Header(alias="X-Session-Id", default=None),
    session: AsyncSession = Depends(get_db)
) -> Cart:
    """Резолвит корзину: авторизованную или гостевую. Всегда возвращает с eager-loaded отношениями."""
    if not customer_id and not session_id:
        raise HTTPException(status_code=401, detail="Требуется Authorization или X-Session-Id")

    stmt = select(Cart).where(
        or_(
            Cart.customer_id == customer_id if customer_id else False,
            Cart.session_id == session_id if session_id else False
        )
    ).options(
        selectinload(Cart.cart_items)
        .selectinload(CartItem.sku)
        .selectinload(SKU.stock)
    )
    
    res = await session.execute(stmt)
    cart = res.scalar_one_or_none()

    if not cart:
        cart = Cart(customer_id=customer_id, session_id=session_id)
        session.add(cart)

    return cart

async def merge_guest_cart(
    session: AsyncSession,
    customer_id: UUID,
    session_id: UUID
) -> Cart | None:
    """
    Сливает гостевую корзину в пользовательскую по правилу max(quantity).
    Не делает commit! Оставляет транзакцию открытой для вызывающего кода.
    """
    user_cart_res = await session.execute(
        select(Cart).where(Cart.customer_id == customer_id)
        .options(selectinload(Cart.cart_items))
    )
    user_cart = user_cart_res.scalar_one_or_none()

    guest_cart_res = await session.execute(
        select(Cart).where(Cart.session_id == session_id)
        .options(selectinload(Cart.cart_items))
    )
    guest_cart = guest_cart_res.scalar_one_or_none()

    if not guest_cart or not guest_cart.cart_items:
        return user_cart

    if not user_cart:
        user_cart = Cart(customer_id=customer_id)
        session.add(user_cart)

    guest_items_map = {item.sku_id: item for item in guest_cart.cart_items}
    
    for user_item in user_cart.cart_items:
        if user_item.sku_id in guest_items_map:
            guest_item = guest_items_map.pop(user_item.sku_id)
            user_item.quantity = max(user_item.quantity, guest_item.quantity)
            if user_item.unit_price_at_add is None:
                user_item.unit_price_at_add = guest_item.unit_price_at_add

    for sku_id, guest_item in guest_items_map.items():
        new_item = CartItem(
            cart_id=user_cart.id,
            sku_id=sku_id,
            quantity=guest_item.quantity,
            unit_price_at_add=guest_item.unit_price_at_add
        )
        session.add(new_item)

    await session.delete(guest_cart)

    return user_cart