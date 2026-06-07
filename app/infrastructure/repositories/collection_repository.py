from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.models import Collection, CollectionProduct, Product, SKU


class CollectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_collections(
        self, limit: int, offset: int
    ) -> List[Collection]:
        today = date.today()
        query = (select(Collection)
                 .where(Collection.is_active == True)
                 .where((Collection.start_date <= today) | (Collection.start_date == None))
                 .order_by(Collection.priority)
                 .limit(limit)
                 .offset(offset))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_collections_count(self) -> int:
        today = date.today()
        query = (select(func.count())
                 .select_from(Collection)
                 .where(Collection.is_active == True)
                 .where((Collection.start_date <= today) | (Collection.start_date == None)))
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_collection_by_id(self, collection_id: UUID) -> Optional[Collection]:
        result = await self.session.execute(
            select(Collection).where(Collection.id == collection_id)
        )
        return result.scalar_one_or_none()

    async def get_collection_product_ids(
        self, collection_id: UUID, limit: int, offset: int
    ) -> List[UUID]:
        query = (select(CollectionProduct.product_id)
                 .where(CollectionProduct.collection_id == collection_id)
                 .order_by(CollectionProduct.ordering)
                 .limit(limit)
                 .offset(offset))
        result = await self.session.execute(query)
        return [row[0] for row in result.all()]

    async def get_collection_products_count(self, collection_id: UUID) -> int:
        query = (select(func.count())
                 .select_from(CollectionProduct)
                 .where(CollectionProduct.collection_id == collection_id))
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_products_by_ids(
        self, product_ids: List[UUID]
    ) -> List[Product]:
        """Получить товары по списку ID с подгрузкой SKU и Stock"""
        if not product_ids:
            return []
        query = (select(Product)
                 .where(Product.id.in_(product_ids))
                 .where(Product.status == "MODERATED")
                 .options(
                     selectinload(Product.skus)
                     .selectinload(SKU.stock)
                 ))
        result = await self.session.execute(query)
        return list(result.scalars().all())