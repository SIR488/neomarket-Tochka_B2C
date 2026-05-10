from typing import List, Optional, Any, Dict
from uuid import UUID
from sqlalchemy import select, func, or_, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.models import Product, SKU, CharacteristicValue, Category, Stock
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
            category_cte = (
                select(Category.id, Category.parent_id)
                .where(Category.id == category_id)
                .cte(name="category_tree", recursive="True")
            )

            category_cte = category_cte.union_all(
                select(Category.id, Category.parent_id)
                .join(category_cte, Category.id == category_cte.c.parent_id)
            )

            query = query.where(Product.category_id.in_(select(category_cte.c.id)))

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
            match sort:
                case SortOption.price_asc | SortOption.price_desc:
                    min_price_subq = (
                        select(SKU.product_id, func.min(SKU.price).label("min_price"))
                        .where(SKU.status == "ACTIVE")
                        .group_by(SKU.product_id)
                        .subquery()
                    )

                    query = query.join(
                        min_price_subq, Product.id == min_price_subq.c.product_id
                    )

                    if sort == SortOption.price_asc:
                        query = query.order_by(min_price_subq.c.min_price.asc())
                    else:
                        query = query.order_by(min_price_subq.c.min_price.desc())

                case SortOption.date_desc:
                    query = query.order_by(Product.created_at.desc())

                case SortOption.popularity:
                    query = query.order_by(Product.orders_count.desc())

                case SortOption.rating:
                    query = query.order_by(Product.rating.desc())

                case SortOption.discount_desc:
                    discount_subq = (
                        select(SKU.product_id,
                               func.max(SKU.old_price - SKU.price).label("max_discount")
                        )
                        .where(SKU.status == "ACTIVE")
                        .where(SKU.old_price > SKU.price)
                        .group_by(SKU.product_id)
                        .subquery()
                    )
                    query = query.outerjoin(
                        discount_subq, Product.id == discount_subq.c.product_id
                    )

                    query = query.order_by(
                        func.coalesce(discount_subq.c.max_discount, 0).desc()
                    )



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
    
    async def get_facets(
        self, 
        category_id: UUID, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[str, str, int]]:
        query = (
            select(
                CharacteristicValue.name,
                CharacteristicValue.value,
                func.count(distinct(Product.id)).label("count")
            )
            .join(SKU, SKU.product_id == Product.id)
            .join(CharacteristicValue, CharacteristicValue.sku_id == SKU.id)
            .where(
                Product.category_id == category_id,
                Product.status == "MODERATED",
                SKU.status == "ACTIVE"
            )
        )

        if filters:
            for attr_name, attr_values in filters.items():
                if not isinstance(attr_values, list):
                    attr_values = [attr_values]

                subq = (
                    select(SKU.product_id)
                    .join(CharacteristicValue)
                    .where(
                        CharacteristicValue.name == attr_name.upper(),
                        CharacteristicValue.value.in_(attr_values)
                    )
                )
                query = query.where(Product.id.in_(subq))

        query = query.group_by(CharacteristicValue.name, CharacteristicValue.value)
        
        result = await self.session.execute(query)
        return result.all()
    
    async def get_sku_with_details(self, product_id: UUID, sku_id: UUID) -> Optional[SKU]:
        query = (
            select(SKU)
            .options(
                selectinload(SKU.characteristics),
                selectinload(SKU.stock),
                selectinload(SKU.product)
            )
            .where(
                SKU.id == sku_id,
                SKU.product_id == product_id
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
