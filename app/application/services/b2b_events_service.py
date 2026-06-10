from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from typing import Dict, Any

from app.infrastructure.models import B2BEventIdempotency, CartItem, SKU, Product


class B2BEventsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_b2b_event(self, event_type: str, idempotency_key: UUID, payload: Dict[str, Any]):
        # 1. Проверка идемпотентности
        existing = await self.session.get(B2BEventIdempotency, idempotency_key)
        if existing:
            return {"status": "ignored", "reason": "already_processed"}
        
        # 2. Записываем ключ идемпотентности
        occurred_at = payload.get("occurred_at")
        if occurred_at and isinstance(occurred_at, str):
            occurred_at = datetime.fromisoformat(occurred_at.replace('Z', '+00:00'))
        
        event_record = B2BEventIdempotency(
            idempotency_key=idempotency_key,
            occurred_at=occurred_at or datetime.now(timezone.utc)
        )
        self.session.add(event_record)
        
        # 3. Обработка событий
        if event_type in ("PRODUCT_BLOCKED", "PRODUCT_HARD_BLOCKED", "PRODUCT_DELETED"):
            product_id_str = payload.get("product_id")
            if product_id_str:
                product_id = UUID(product_id_str)
                # Обновляем статус продукта
                product = await self.session.get(Product, product_id)
                if product:
                    product.status = "BLOCKED" if event_type != "PRODUCT_DELETED" else "DELETED"
                    self.session.add(product)
                
                # Находим все SKU этого продукта
                skus_query = select(SKU.id).where(SKU.product_id == product_id)
                skus_result = await self.session.execute(skus_query)
                sku_ids = list(skus_result.scalars().all())
                
                if sku_ids:
                    reason = "PRODUCT_DELETED" if event_type == "PRODUCT_DELETED" else "PRODUCT_BLOCKED"
                    stmt = (
                        update(CartItem)
                        .where(CartItem.sku_id.in_(sku_ids))
                        .where(CartItem.unavailable_reason.is_(None))
                        .values(unavailable_reason=reason)
                    )
                    await self.session.execute(stmt)
                    
        elif event_type == "SKU_OUT_OF_STOCK":
            sku_id_str = payload.get("sku_id")
            if sku_id_str:
                sku_id = UUID(sku_id_str)
                stmt = (
                    update(CartItem)
                    .where(CartItem.sku_id == sku_id)
                    .where(CartItem.unavailable_reason.is_(None))
                    .values(unavailable_reason="OUT_OF_STOCK")
                )
                await self.session.execute(stmt)
        
        elif event_type == "SKU_BACK_IN_STOCK":
            sku_id_str = payload.get("sku_id")
            if sku_id_str:
                sku_id = UUID(sku_id_str)
                stmt = (
                    update(CartItem)
                    .where(CartItem.sku_id == sku_id)
                    .values(unavailable_reason=None)
                )
                await self.session.execute(stmt)
        
        elif event_type == "PRICE_CHANGED":
            sku_id_str = payload.get("sku_id")
            if sku_id_str:
                sku_id = UUID(sku_id_str)
                # Обновляем цену в SKU
                new_price = payload.get("new_price")
                if new_price:
                    stmt = update(SKU).where(SKU.id == sku_id).values(price=new_price)
                    await self.session.execute(stmt)
        
        await self.session.commit()
        return {"status": "processed"}