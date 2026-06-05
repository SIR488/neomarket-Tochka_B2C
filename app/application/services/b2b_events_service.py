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
            
        # Записываем ключ идемпотентности
        self.session.add(B2BEventIdempotency(idempotency_key=idempotency_key))
        
        # 2. Обработка событий
        if event_type in ("PRODUCT_BLOCKED", "PRODUCT_HARD_BLOCKED", "PRODUCT_DELETED"):
            product_id_str = payload.get("product_id")
            if product_id_str:
                product_id = UUID(product_id_str)
                # Обновляем статус продукта (опционально, если нужно локально синхронизировать)
                product = await self.session.get(Product, product_id)
                if product:
                    product.status = event_type
                    self.session.add(product)
                
                # Находим все SKU этого продукта
                skus_query = select(SKU.id).where(SKU.product_id == product_id)
                skus_result = await self.session.execute(skus_query)
                sku_ids = [row for row in skus_result.scalars().all()]
                
                if sku_ids:
                    # Обновляем CartItem, помечая как unavailable
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
                
        await self.session.commit()
        return {"status": "processed"}
