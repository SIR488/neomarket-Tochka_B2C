from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.models import Category
from sqlalchemy import func
from app.infrastructure.models import Product

class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_active(self) -> List[Category]:
        """Получить все активные категории для построения дерева"""
        
        query = select(Category).where(Category.is_active == True).order_by(Category.name)
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
