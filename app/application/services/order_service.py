from typing import List, Optional
from uuid import UUID
from uuid6 import uuid7
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.infrastructure.models import Order, OrderItem, SKU, Product, PaymentMethod, Cart, CartItem, Address
from app.api.v1.schemas.order import OrderCreateRequest, OrderItemRequest
from app.infrastructure.b2b_client import B2BClient, B2BUnavailableError

class OrderService:
    def __init__(self, session: AsyncSession, b2b_client: B2BClient):
        self.session = session
        self.b2b_client = b2b_client

    async def create_order(self, user_id: UUID, request: OrderCreateRequest, idempotency_key: UUID) -> Order:
        # 0. Idempotency check
        existing = await self.session.execute(
            select(Order).options(selectinload(Order.items), selectinload(Order.address)).where(Order.idempotency_key == idempotency_key)
        )
        existing_order = existing.scalars().first()
        if existing_order:
            return existing_order

        # 1. Fetch cart and cart_items
        cart_query = select(Cart).options(
            selectinload(Cart.cart_items).selectinload(CartItem.sku).selectinload(SKU.product),
            selectinload(Cart.cart_items).selectinload(CartItem.sku).selectinload(SKU.stock)
        ).where(Cart.customer_id == user_id)
        cart_result = await self.session.execute(cart_query)
        cart = cart_result.scalars().first()

        if not cart or not cart.cart_items:
            raise HTTPException(status_code=400, detail={"code": "EMPTY_CART", "message": "Корзина пуста"})

        request_items = cart.cart_items

        # 2. Проверка наличия
        failed = []
        for item in request_items:
            sku = item.sku
            if not sku:
                failed.append({"sku_id": str(item.sku_id), "reason": "SKU_NOT_FOUND"})
                continue
            
            if sku.product.status != "MODERATED":
                failed.append({"sku_id": str(item.sku_id), "reason": "PRODUCT_BLOCKED"})
                continue
                
            avail_qty = sku.stock.quantity if sku.stock else 0
            if avail_qty < item.quantity:
                reason = "INSUFFICIENT_STOCK" if avail_qty > 0 else "OUT_OF_STOCK"
                failed.append({
                    "sku_id": str(item.sku_id),
                    "reason": reason,
                    "requested": item.quantity,
                    "available": avail_qty
                })

        if failed:
            raise HTTPException(status_code=409, detail={"code": "RESERVE_FAILED", "message": "Не удалось зарезервировать товары", "failed_items": failed})

        # 2.5 Проверка payment_method_id и address_id
        if request.payment_method_id:
            pm = await self.session.get(PaymentMethod, request.payment_method_id)
            if not pm or pm.customer_id != user_id:
                raise HTTPException(status_code=400, detail={"code": "INVALID_PAYMENT_METHOD", "message": "Способ оплаты не найден или принадлежит другому пользователю"})
                
        address = await self.session.get(Address, request.address_id)
        if not address or address.customer_id != user_id:
            raise HTTPException(status_code=400, detail={"code": "INVALID_ADDRESS", "message": "Адрес доставки не найден или принадлежит другому пользователю"})

        # 3. Резервирование в B2B
        order_id = uuid7()
        reserve_items = [{"sku_id": item.sku_id, "quantity": item.quantity} for item in request_items]
        try:
            reserve_result = await self.b2b_client.reserve(idempotency_key, order_id, reserve_items)
        except B2BUnavailableError as e:
            raise HTTPException(status_code=503, detail={"code": "B2B_UNAVAILABLE", "message": str(e)})

        if reserve_result["status"] != 200 or reserve_result.get("data", {}).get("status") != "RESERVED":
            # B2B returned failure (e.g. 409)
            failed_items = reserve_result.get("data", {}).get("failed_items", [])
            raise HTTPException(status_code=409, detail={"code": "RESERVE_FAILED", "message": "Не удалось зарезервировать товары", "failed_items": failed_items})

        # 4. Создание заказа
        total_amount = sum(item.sku.price * item.quantity for item in request_items)
        
        order = Order(
            id=order_id,
            user_id=user_id,
            status="PAID",
            total_amount=total_amount,
            address_id=request.address_id,
            payment_method_id=request.payment_method_id,
            idempotency_key=idempotency_key
        )
        self.session.add(order)
        await self.session.flush()

        for item in request_items:
            sku = item.sku
            order_item = OrderItem(
                order_id=order.id,
                sku_id=item.sku_id,
                product_id=sku.product_id,
                product_title=sku.product.title,
                sku_name=sku.name,
                quantity=item.quantity,
                unit_price=sku.price,
                line_total=sku.price * item.quantity
            )
            self.session.add(order_item)
            
        # Очищаем корзину
        await self.session.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
        
        await self.session.commit()
        await self.session.refresh(order)
        
        # Load items and address for response
        await self.session.execute(select(Order).options(selectinload(Order.items), selectinload(Order.address)).where(Order.id == order.id))
        return order

    async def get_orders(self, user_id: UUID, limit: int = 20, offset: int = 0, status: Optional[str] = None) -> dict:
        from sqlalchemy import func
        
        count_query = select(func.count()).select_from(Order).where(Order.user_id == user_id)
        if status:
            count_query = count_query.where(Order.status == status)
        total_count = await self.session.scalar(count_query)
        
        query = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.address))
            .where(Order.user_id == user_id)
        )
        if status:
            query = query.where(Order.status == status)
            
        query = query.order_by(Order.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        orders = result.scalars().all()
        
        return {
            "items": orders,
            "total_count": total_count or 0,
            "limit": limit,
            "offset": offset
        }

    async def get_order_by_id(self, user_id: UUID, order_id: UUID) -> Order:
        query = select(Order).options(selectinload(Order.items), selectinload(Order.address)).where(Order.id == order_id)
        result = await self.session.execute(query)
        order = result.scalars().first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
            
        if order.user_id != user_id:
            raise HTTPException(status_code=404, detail="Заказ не найден")
            
        return order

    async def cancel_order(self, user_id: UUID, order_id: UUID) -> Order:
        order = await self.get_order_by_id(user_id, order_id)
        
        if order.status not in ["CREATED", "PAID"]:
            raise HTTPException(status_code=409, detail={"code": "CANCEL_NOT_ALLOWED", "message": "Невозможно отменить заказ в текущем статусе", "current_status": order.status})
            
        items_payload = [{"sku_id": str(item.sku_id), "quantity": item.quantity} for item in order.items]
        
        try:
            reserve_result = await self.b2b_client.unreserve(order.id, items_payload)
            if reserve_result["status"] == 200:
                order.status = "CANCELLED"
            else:
                # Если B2B ответил ошибкой (не 200), переводим в CANCEL_PENDING для повтора
                order.status = "CANCEL_PENDING"
        except B2BUnavailableError:
            # Если B2B недоступен по таймауту/503, тоже CANCEL_PENDING
            order.status = "CANCEL_PENDING"
            
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def update_order_status(self, user_id: UUID, order_id: UUID, new_status: str) -> Order:
        query = select(Order).options(selectinload(Order.items), selectinload(Order.address)).where(Order.id == order_id)
        result = await self.session.execute(query)
        order = result.scalars().first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
            
        if order.user_id != user_id:
            raise HTTPException(status_code=404, detail="Заказ не найден")
            
        valid_transitions = {
            "CREATED": ["PAID", "CANCELLED"],
            "PAID": ["ASSEMBLING", "DELIVERED", "CANCEL_PENDING", "CANCELLED"],
            "ASSEMBLING": ["DELIVERING"],
            "DELIVERING": ["DELIVERED"],
        }
        
        if new_status not in valid_transitions.get(order.status, []):
             raise HTTPException(status_code=409, detail={"code": "INVALID_TRANSITION", "message": f"Недопустимый переход из {order.status} в {new_status}"})
            
        old_status = order.status
        order.status = new_status
        
        if new_status == "DELIVERED" and old_status != "DELIVERED":
            items_payload = [{"sku_id": str(item.sku_id), "quantity": item.quantity} for item in order.items]
            try:
                fulfill_result = await self.b2b_client.fulfill(order.id, items_payload)
                if fulfill_result["status"] == 200:
                    order.fulfill_called = True
                else:
                    order.fulfill_called = False
            except B2BUnavailableError:
                order.fulfill_called = False
                
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order
