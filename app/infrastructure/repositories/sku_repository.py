from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from uuid import UUID

from app.infrastructure.models import SKU

class SKURepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_with_stock(self, sku_id: UUID) -> SKU | None:
        result = await self.session.execute(
            select(SKU).where(SKU.id == sku_id)
        )
        return result.scalar_one_or_none()

    async def get_available_quantity(self, sku_id: UUID) -> int:
        sku = await self.get_with_stock(sku_id)
        if not sku or not sku.stock:
            return 0
        return sku.stock.quantity