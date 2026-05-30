from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID

from app.infrastructure.models import B2BEventIdempotency, CartItem, SKU, Product

class B2BEventsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_product_event(self, idempotency_key: UUID, product_id: UUID, status: str):
        # 1. Проверка идемпотентности
        existing = await self.session.get(B2BEventIdempotency, idempotency_key)
        if existing:
            return {"status": "ignored", "reason": "already_processed"}
            
        # Записываем ключ идемпотентности
        self.session.add(B2BEventIdempotency(idempotency_key=idempotency_key))
        
        # Обновляем статус продукта (опционально, если нужно локально синхронизировать)
        product = await self.session.get(Product, product_id)
        if product:
            product.status = status
            self.session.add(product)
            
        # 2. Обработка блокировки товара (если статус не MODERATED, товар недоступен)
        if status != "MODERATED":
            # Находим все SKU этого продукта
            skus_query = select(SKU.id).where(SKU.product_id == product_id)
            skus_result = await self.session.execute(skus_query)
            sku_ids = [row for row in skus_result.scalars().all()]
            
            if sku_ids:
                # Обновляем CartItem, помечая как unavailable
                stmt = (
                    update(CartItem)
                    .where(CartItem.sku_id.in_(sku_ids))
                    .where(CartItem.unavailable_reason.is_(None))
                    .values(unavailable_reason="PRODUCT_BLOCKED")
                )
                await self.session.execute(stmt)
                
        await self.session.commit()
        return {"status": "processed"}
