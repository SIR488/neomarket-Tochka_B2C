from typing import Optional, List
from uuid import UUID

from app.infrastructure.models import Favorite
from app.infrastructure.repositories.favorites_repository import FavoriteRepository

class FavoritesService:
    def __init__(self, repository: FavoriteRepository):
        self.repository = repository


    async def add_to_favorites(self, customer_id: UUID, product_id: UUID) -> Optional[UUID]:
        result = await self.repository.add_favorite(customer_id, product_id)

        if not result:
            return None

        return result


    async def get_favorites(self, customer_id: UUID, limit: int = 10, offset: int = 0) -> Optional[List[Favorite]]:
        result = await self.repository.get_favorites(customer_id, limit, offset)

        if not result:
            return None

        return result

    async def remove_favorite(self, customer_id: UUID, product_id: UUID) -> Optional[UUID]:
        result = await self.repository.delete_favorite(customer_id, product_id)

        if not result:
            return None

        return result
