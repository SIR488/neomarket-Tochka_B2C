from typing import List
from uuid import UUID
from fastapi import HTTPException

from app.infrastructure.repositories.collection_repository import CollectionRepository
from app.infrastructure.b2b_client import B2BClient, B2BUnavailableError
from app.api.v1.schemas.collection import CollectionResponse
from app.api.v1.schemas.catalog import CatalogProductCard, ImageRef
from uuid6 import uuid7


class CollectionService:
    def __init__(self, repository: CollectionRepository, b2b_client: B2BClient):
        self.repository = repository
        self.b2b_client = b2b_client

    async def get_collections(self) -> List[CollectionResponse]:
        collections = await self.repository.get_active_collections()
        items = []
        
        for c in collections:
            product_ids = await self.repository.get_all_collection_product_ids(c.id)
            
            try:
                products_data = await self.b2b_client.get_products_by_ids(product_ids)
            except B2BUnavailableError:
                raise HTTPException(status_code=503, detail="B2B service unavailable")
            
            product_cards = []
            for pid in product_ids:
                product = products_data.get(pid)
                if not product:
                    continue
                
                images = []
                if product.get("image_url"):
                    images.append(ImageRef(
                        id=uuid7(),
                        url=product["image_url"],
                        alt=product.get("title", ""),
                        ordering=0,
                        is_main=True
                    ))
                
                product_cards.append(
                    CatalogProductCard(
                        id=pid,
                        name=product.get("title", ""),
                        min_price=product.get("price", 0),
                        has_stock=product.get("available_quantity", 0) > 0,
                        images=images,
                        old_price=product.get("old_price"),
                        rating=product.get("rating"),
                        reviews_count=product.get("reviews_count", 0)
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
        
        return items