from typing import List, Optional, Any, Dict
from uuid import UUID
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.models import Product, SKU, CharacteristicValue, Stock
from app.api.v1.schemas.catalog import SortOption

class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self,
        limit: int = 10,
        offset: int = 0,
        category_id: Optional[UUID] = None,
        sort: Optional[SortOption] = None,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> (List[Product], int):
        """
        Получить список товаров с фильтрацией и поиском.
        Возвращает кортеж (список товаров, общее количество).
        """

        query = select(Product).options(
            selectinload(Product.skus).selectinload(SKU.stock)
        ).where(Product.status == "MODERATED")

        if category_id:
            query = query.where(Product.category_id == category_id)

        if search and len(search) >= 3:
            query = query.where(
                or_(
                    Product.title.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%")
                )
            )

        if filters:
            for attr_name, attr_values in filters.items():
                if not isinstance(attr_values, list):
                    attr_values = [attr_values]
                
                sku_subquery = select(SKU.product_id).join(CharacteristicValue).where(
                    and_(
                        CharacteristicValue.name == attr_name.upper(),
                        CharacteristicValue.value.in_(attr_values)
                    )
                )
                query = query.where(Product.id.in_(sku_subquery))

        if sort:
            if sort == SortOption.price_asc:
                query = query.join(SKU).order_by(SKU.price.asc())
            elif sort == SortOption.price_desc:
                query = query.join(SKU).order_by(SKU.price.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total_count = await self.session.execute(count_query)
        total = total_count.scalar() or 0

        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)

        return list(result.scalars().unique().all()), total

    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """Получить полную информацию о товаре со всеми SKU и характеристиками"""
        
        query = select(Product).options(
            selectinload(Product.skus).selectinload(SKU.characteristics),
            selectinload(Product.skus).selectinload(SKU.stock),
            selectinload(Product.category)
        ).where(Product.id == product_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
