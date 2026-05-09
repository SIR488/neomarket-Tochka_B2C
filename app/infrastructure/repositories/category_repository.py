from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.models import Category
from sqlalchemy import func
from app.infrastructure.models import Product, CharacteristicValue, SKU

class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_active(self) -> List[Category]:
        """Получить все активные категории для построения дерева"""
        
        query = select(Category).where(Category.is_active.is_(True)).order_by(Category.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, category_id: UUID) -> Optional[Category]:
        """Получить категорию по ID"""

        query = select(Category).where(Category.id == category_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_product_count(self, category_id: UUID) -> int:
        """Подсчет количества товаров в категории (включая подкатегории)"""

        query = select(func.count(Product.id)).where(Product.category_id == category_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_by_slug(self, slug: str) -> Optional[Category]:
        """Получить категорию по слагу"""

        query = select(Category).where(Category.slug == slug)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_category_filters(self, category_id: UUID):
        """
        Возвращает:
        - характеристики товаров категории (name -> [values])
        - min/max цену
        """

        category_exists = await self.get_by_id(category_id)
        if not category_exists:
            return None

        chars_query = (
            select(
                CharacteristicValue.name,
                CharacteristicValue.value
            )
            .join(SKU, SKU.id == CharacteristicValue.sku_id)
            .join(Product, Product.id == SKU.product_id)
            .where(
                Product.category_id == category_id,
                Product.status == "MODERATED",
                SKU.status == "ACTIVE"
            )
            .distinct()
            .order_by(CharacteristicValue.name, CharacteristicValue.value)
        )

        chars_result = await self.session.execute(chars_query)
        rows = chars_result.all()

        price_query = (
            select(
                func.min(SKU.price).label("min_price"),
                func.max(SKU.price).label("max_price")
            )
            .join(Product, Product.id == SKU.product_id)
            .where(
                Product.category_id == category_id,
                Product.status == "MODERATED",
                SKU.status == "ACTIVE"
            )
        )

        price_result = await self.session.execute(price_query)
        price_row = price_result.one()

        return {
            "characteristics": rows,           # [(name, value), ...]
            "min_price": price_row.min_price,
            "max_price": price_row.max_price,
        }
    
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
