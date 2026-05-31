from sqlite3 import IntegrityError
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.models import Favorite, Product

class FavoriteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_favorite(self, customer_id: UUID, product_id: UUID) -> Optional[UUID]:
        product = await self.session.get(Product, product_id)
        if not product:
            return None

        fav = Favorite(customer_id=customer_id, product_id=product_id)
        self.session.add(fav)
        try:
            await self.session.commit()
            await self.session.refresh(fav)
        except IntegrityError:
            await self.session.rollback()
            return None

        return fav.id

    async def get_favorites(self, customer_id: UUID, limit: int = 10, offset: int = 0) -> List[Favorite]:
        query = select(Favorite).where(Favorite.customer_id == customer_id).limit(limit).offset(offset)
        result = await self.session.execute(query)
        favorites = result.scalars().all()
        return list(favorites)

    async def delete_favorite(self, customer_id: UUID, product_id: UUID) -> Optional[UUID]:
        query = select(Favorite).where(Favorite.customer_id == customer_id, Favorite.product_id == product_id)
        result = await self.session.execute(query)

        favorite = result.scalar_one_or_none()
        if not favorite:
            return None

        await self.session.delete(favorite)
        await self.session.commit()

        return favorite.id