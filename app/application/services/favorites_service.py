from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException

from app.infrastructure.models import Favorite
from app.infrastructure.repositories.favorites_repository import FavoriteRepository
from app.api.v1.schemas.favorite import SubscriptionEventType
from app.api.v1.schemas.catalog import ProductShortListResponse, ProductShort

class FavoritesService:
    def __init__(self, repository: FavoriteRepository):
        self.repository = repository

    async def add_to_favorites(self, customer_id: UUID, product_id: UUID) -> bool:
        return await self.repository.add_favorite(customer_id, product_id)

    async def get_favorites(self, customer_id: UUID, limit: int, offset: int) -> ProductShortListResponse:
        favorites = await self.repository.get_favorites(customer_id, limit, offset)
        
        items = []
        for fav in favorites:
            product = fav.product
            if not product:
                continue
            
            active_sku = next((sku for sku in product.skus if sku.status == "ACTIVE"), None)
            price = active_sku.price if active_sku else 0
            in_stock = False
            if active_sku and active_sku.stock:
                in_stock = active_sku.stock.quantity > 0
            
            items.append(
                ProductShort(
                    id=fav.product_id,
                    title=product.title,
                    price=price,
                    in_stock=in_stock,
                    is_in_cart=False,
                    image=product.image_url
                )
            )
        
        return ProductShortListResponse(
            items=items,
            total_count=len(favorites),
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
    ) -> dict:
        """Подписаться на уведомления о товаре"""
        product = await self.repository.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        results = {"success": [], "failed": []}
        
        for event in events:
            success = await self.repository.add_subscription(customer_id, product_id, event)
            if success:
                results["success"].append(event)
            else:
                results["failed"].append({"event": event, "reason": "Already subscribed"})
        
        return results

    async def unsubscribe_from_product(
        self, 
        customer_id: UUID, 
        product_id: UUID,
        event_type: SubscriptionEventType = None
    ) -> int:
        """Отписаться от уведомлений о товаре"""
        return await self.repository.remove_subscription(customer_id, product_id, event_type)