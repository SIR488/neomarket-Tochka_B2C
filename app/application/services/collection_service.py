from typing import List, Tuple
from uuid import UUID
from fastapi import HTTPException

from app.infrastructure.repositories.collection_repository import CollectionRepository
from app.api.v1.schemas.collection import (
    CollectionResponse, CollectionsListResponse
)
from app.api.v1.schemas.catalog import CatalogProductCard, ImageRef
from uuid6 import uuid7


class CollectionService:
    def __init__(self, repository: CollectionRepository):
        self.repository = repository

    async def get_collections(
        self, limit: int, offset: int
    ) -> CollectionsListResponse:
        collections = await self.repository.get_active_collections(limit, offset)
        total_count = await self.repository.get_active_collections_count()
        
        items = []
        for c in collections:
            product_ids = await self.repository.get_collection_product_ids(c.id, limit=100, offset=0)
            products = await self.repository.get_products_by_ids(product_ids)
            
            product_cards = []
            for product in products:
                active_sku = next((sku for sku in product.skus if sku.status == "ACTIVE"), None)
                price = active_sku.price if active_sku else 0
                has_stock = False
                if active_sku and active_sku.stock:
                    has_stock = active_sku.stock.quantity > 0
                
                # Создаём ImageRef
                images = []
                if product.image_url:
                    images.append(ImageRef(
                        id=uuid7(),
                        url=product.image_url,
                        alt=product.title,
                        ordering=0,
                        is_main=True
                    ))
                
                product_cards.append(
                    CatalogProductCard(
                        id=product.id,
                        name=product.title,
                        min_price=price,
                        has_stock=has_stock,
                        images=images,
                        old_price=active_sku.old_price if active_sku else None,
                        rating=product.rating if product.rating else None,
                        reviews_count=product.orders_count or 0
                    )
                )
            
            items.append(
                CollectionResponse(
                    id=c.id,
                    name=c.title,
                    description=c.description,
                    cover_image_url=c.cover_image_url,
                    target_url=c.target_url,
                    priority=c.priority,
                    products=product_cards
                )
            )
        
        return CollectionsListResponse(
            items=items,
            total_count=total_count,
            limit=limit,
            offset=offset
        )