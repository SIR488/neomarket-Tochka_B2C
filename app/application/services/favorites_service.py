from typing import List, Optional
from uuid import UUID
from uuid6 import uuid7
from fastapi import HTTPException

from app.infrastructure.models import Favorite
from app.infrastructure.repositories.favorites_repository import FavoriteRepository
from app.api.v1.schemas.favorite import SubscriptionEventType
from app.api.v1.schemas.catalog import PaginatedCatalogProducts, CatalogProductCard, ImageRef


class FavoritesService:
    def __init__(self, repository: FavoriteRepository):
        self.repository = repository

    async def add_to_favorites(self, customer_id: UUID, product_id: UUID) -> bool:
        return await self.repository.add_favorite(customer_id, product_id)


    async def get_favorites(self, customer_id: UUID, limit: int, offset: int) -> PaginatedCatalogProducts:
        favorites = await self.repository.get_favorites(customer_id, limit, offset)
        
        total_count = await self.repository.get_favorites_count(customer_id)
        
        items = []
        for fav in favorites:
            product = fav.product
            if not product:
                continue
            
            active_sku = next((sku for sku in product.skus if sku.status == "ACTIVE"), None)
            price = active_sku.price if active_sku else 0
            has_stock = False
            if active_sku and active_sku.stock:
                has_stock = active_sku.stock.quantity > 0
            
            images = []
            if product.image_url:
                images.append(ImageRef(
                    id=uuid7(),
                    url=product.image_url,
                    alt=product.title,
                    ordering=0,
                    is_main=True
                ))
            
            items.append(
                CatalogProductCard(
                    id=fav.product_id,
                    name=product.title,      # name вместо title
                    min_price=price,         # min_price вместо price
                    has_stock=has_stock,     # has_stock вместо in_stock
                    images=images,           # список ImageRef вместо строки
                    old_price=active_sku.old_price if active_sku else None,
                    rating=product.rating if product.rating else None,
                    reviews_count=product.orders_count or 0
                )
            )
        
        return PaginatedCatalogProducts(
            items=items,
            total_count=total_count,  # правильный total_count (отдельный запрос)
            limit=limit,
            offset=offset
        )

    async def remove_favorite(self, customer_id: UUID, product_id: UUID) -> bool:
        return await self.repository.delete_favorite(customer_id, product_id)


    async def subscribe_to_product(
        self, 
        customer_id: UUID, 
        product_id: UUID, 
        events: List[SubscriptionEventType]
    ) -> str:
        """Возвращает: 'SUCCESS', 'PRODUCT_NOT_FOUND', 'ALREADY_SUBSCRIBED'"""
        product = await self.repository.get_product(product_id)
        if not product:
            return "PRODUCT_NOT_FOUND"
        
        for event in events:
            success = await self.repository.add_subscription(customer_id, product_id, event)
            if not success:
                return "ALREADY_SUBSCRIBED"
        
        return "SUCCESS"

    async def unsubscribe_from_product(
        self, 
        customer_id: UUID, 
        product_id: UUID,
        event_type: SubscriptionEventType = None
    ) -> int:
        """Отписаться от уведомлений о товаре"""
        return await self.repository.remove_subscription(customer_id, product_id, event_type)