from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import Collection, CollectionProduct


class CollectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_collections(self) -> List[Collection]:
        """Получить все активные подборки (без пагинации)"""
        today = date.today()
        query = (select(Collection)
                 .where(Collection.is_active == True)
                 .where((Collection.start_date <= today) | (Collection.start_date == None))
                 .order_by(Collection.priority))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_collection_by_id(self, collection_id: UUID) -> Optional[Collection]:
        """Найти подборку по ID"""
        result = await self.session.execute(
            select(Collection).where(Collection.id == collection_id)
        )
        return result.scalar_one_or_none()

    async def get_all_collection_product_ids(self, collection_id: UUID) -> List[UUID]:
        """Получить все product_ids подборки (без пагинации)"""
        query = (select(CollectionProduct.product_id)
                 .where(CollectionProduct.collection_id == collection_id)
                 .order_by(CollectionProduct.ordering))
        result = await self.session.execute(query)
        return [row[0] for row in result.all()]