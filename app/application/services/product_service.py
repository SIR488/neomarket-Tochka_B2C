from typing import Optional, Any, Dict, List
from uuid import UUID
from app.infrastructure.repositories.product_repository import ProductRepository
from app.api.v1.schemas.catalog import (
    ProductShort, 
    ProductShortListResponse, 
    Product, 
    Sku,
    Image, 
    Characteristic,
    SortOption,
    FacetsResponse,
    Facet,
    FacetValue
)

class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def _map_to_short(self, db_product: Any) -> ProductShort:
        """Вспомогательный метод для маппинга в ProductShort"""

        main_sku = db_product.skus[0] if db_product.skus else None
        price = (main_sku.price / 100.0) if main_sku else 0.0
        

        in_stock = any((s.stock.quantity > 0) for s in db_product.skus if s.stock)
        
        return ProductShort(
            id=db_product.id,
            title=db_product.title,
            image=db_product.image_url,
            price=price,
            in_stock=in_stock,
            is_in_cart=False
        )

    async def get_products(
        self,
        limit: int = 10,
        offset: int = 0,
        category_id: Optional[UUID] = None,
        sort: Optional[SortOption] = None,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> ProductShortListResponse:
        items_db, total = await self.repository.get_list(
            limit=limit, offset=offset, category_id=category_id,
            sort=sort, search=search, filters=filters
        )
        
        return ProductShortListResponse(
            total_count=total,
            limit=limit,
            offset=offset,
            items=[self._map_to_short(p) for p in items_db]
        )

    async def get_product_detail(self, product_id: UUID) -> Optional[Product]:
        db_p = await self.repository.get_by_id(product_id)
        if not db_p:
            return None
            
        return Product(
            id=db_p.id,
            slug=db_p.slug,
            title=db_p.title,
            description=db_p.description or "",
            images=[Image(url=db_p.image_url, order=1)] if db_p.image_url else [],
            status=db_p.status,
            characteristics=[],
            skus=[
                Sku(
                    id=s.id,
                    name=s.name,
                    price=s.price / 100.0,
                    quantity=s.stock.quantity if s.stock else 0,
                    characteristics=[
                        Characteristic(name=c.name, value=c.value) 
                        for c in s.characteristics
                    ],
                    images=[Image(url=s.image_url, order=1)] if s.image_url else []
                ) for s in db_p.skus
            ]
        )
    
    async def get_product_facets(
        self, 
        category_id: UUID, 
        filters: Dict[str, Any]
    ) -> FacetsResponse:
        raw_facets = await self.repository.get_facets(category_id, filters)

        temp_map: Dict[str, List[FacetValue]] = {}
        
        for name, value, count in raw_facets:
            if name not in temp_map:
                temp_map[name] = []
            temp_map[name].append(FacetValue(value=value, count=count))
            
        facets_list = [
            Facet(name=name, values=values) 
            for name, values in temp_map.items()
        ]
        
        return FacetsResponse(
            category_id=category_id,
            facets=facets_list
        )
