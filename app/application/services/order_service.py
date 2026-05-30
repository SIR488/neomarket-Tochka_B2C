from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.infrastructure.models import Order, OrderItem, SKU, Product
from app.api.v1.schemas.order import OrderCreateRequest, OrderItemRequest
from app.infrastructure.b2b_client import B2BClient, B2BUnavailableError

class OrderService:
    def __init__(self, session: AsyncSession, b2b_client: B2BClient):
        self.session = session
        self.b2b_client = b2b_client

    async def create_order(self, user_id: UUID, request: OrderCreateRequest) -> Order:
        # 0. Idempotency check
        existing = await self.session.execute(
            select(Order).options(selectinload(Order.items)).where(Order.idempotency_key == request.idempotency_key)
        )
        existing_order = existing.scalars().first()
        if existing_order:
            return existing_order

        # 1. Валидация items
        if not request.items:
            raise HTTPException(status_code=400, detail={"code": "INVALID_REQUEST", "message": "Список items не может быть пустым"})
        for item in request.items:
            if item.quantity < 1:
                raise HTTPException(status_code=422, detail={"code": "INVALID_QUANTITY", "message": "Количество должно быть не менее 1 для каждой позиции"})

        # 2. Проверка наличия
        sku_ids = [item.sku_id for item in request.items]
        query = select(SKU).options(selectinload(SKU.product), selectinload(SKU.stock)).where(SKU.id.in_(sku_ids))
        result = await self.session.execute(query)
        skus = {s.id: s for s in result.scalars().all()}

        failed = []
        for item in request.items:
            sku = skus.get(item.sku_id)
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

        # 3. Резервирование в B2B
        reserve_items = [{"sku_id": item.sku_id, "quantity": item.quantity} for item in request.items]
        try:
            reserve_result = await self.b2b_client.reserve(request.idempotency_key, reserve_items)
        except B2BUnavailableError as e:
            raise HTTPException(status_code=503, detail={"code": "B2B_UNAVAILABLE", "message": str(e)})

        if reserve_result["status"] != 200 or not reserve_result.get("data", {}).get("reserved"):
            # B2B returned failure (e.g. 409)
            failed_items = reserve_result.get("data", {}).get("failed_items", [])
            raise HTTPException(status_code=409, detail={"code": "RESERVE_FAILED", "message": "Не удалось зарезервировать товары", "failed_items": failed_items})

        # 4. Создание заказа
        total_amount = sum(skus[item.sku_id].price * item.quantity for item in request.items)
        
        order = Order(
            user_id=user_id,
            status="PAID",
            total_amount=total_amount,
            delivery_address=request.delivery_address,
            idempotency_key=request.idempotency_key
        )
        self.session.add(order)
        await self.session.flush()

        for item in request.items:
            sku = skus[item.sku_id]
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
        
        await self.session.commit()
        await self.session.refresh(order)
        
        # Load items for response
        await self.session.execute(select(Order).options(selectinload(Order.items)).where(Order.id == order.id))
        return order
