from typing import List, Tuple
from uuid import UUID
from fastapi import HTTPException

from app.infrastructure.repositories.collection_repository import CollectionRepository
from app.api.v1.schemas.collection import (
    CollectionResponse, CollectionsListResponse,
    CollectionProductsResponse
)
from app.api.v1.schemas.catalog import ProductShort


class CollectionService:
    def __init__(self, repository: CollectionRepository):
        self.repository = repository

    async def get_collections(
        self, limit: int, offset: int
    ) -> CollectionsListResponse:
        collections = await self.repository.get_active_collections(limit, offset)
        total_count = await self.repository.get_active_collections_count()
        
        items = [
            CollectionResponse(
                id=c.id,
                title=c.title,
                description=c.description,
                cover_image_url=c.cover_image_url,
                target_url=c.target_url,
                priority=c.priority
            )
            for c in collections
        ]
        
        return CollectionsListResponse(
            items=items,
            total_count=total_count,
            limit=limit,
            offset=offset
        )

    async def get_collection_products(
        self, collection_id: UUID, limit: int, offset: int
    ) -> CollectionProductsResponse:
        # 1. Найти подборку
        collection = await self.repository.get_collection_by_id(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # 2. Получить product_ids из подборки
        product_ids = await self.repository.get_collection_product_ids(
            collection_id, limit, offset
        )
        total_count = await self.repository.get_collection_products_count(collection_id)
        
        # 3. Получить товары из БД
        products = await self.repository.get_products_by_ids(product_ids)
        
        # 4. Разделить на доступные и недоступные
        available_products_map = {p.id: p for p in products}
        items = []
        unavailable_ids = []
        
        for pid in product_ids:
            product = available_products_map.get(pid)
            if product:
                # Берём первый активный SKU
                active_sku = next(
                    (sku for sku in product.skus if sku.status == "ACTIVE"), 
                    None
                )
                price = active_sku.price if active_sku else 0
                in_stock = False
                if active_sku and active_sku.stock:
                    in_stock = active_sku.stock.quantity > 0
                
                items.append(
                    ProductShort(
                        id=product.id,
                        title=product.title,
                        price=price,
                        in_stock=in_stock,
                        is_in_cart=False,
                        image=product.image_url
                    )
                )
            else:
                unavailable_ids.append(pid)
        
        return CollectionProductsResponse(
            collection_id=collection_id,
            title=collection.title,
            items=items,
            unavailable_ids=unavailable_ids,
            total_count=total_count,
            limit=limit,
            offset=offset
        )