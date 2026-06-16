from typing import Any
from uuid import UUID

from app.api.v1.schemas.catalog import ProductShortListResponse, Product, SkuShort, ProductShort, CatalogProductCard
from app.infrastructure.b2b_client import B2BClient


class ProductService:
    def __init__(self):
        self.b2b_client = B2BClient()

    async def get_products(
            self,
            limit: int = 10,
            offset: int = 0,
            sort: str | None = None,
            search: str | None = None,
            filters: dict[str, Any] | None = None,
    ) -> ProductShortListResponse:

        params = {
            "limit": limit,
            "offset": offset,
        }

        if sort:
            params["sort"] = sort
        if search:
            params["search"] = search

        if filters:
            for key, value in filters.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, list):
                            params[f"filter[{key}][{sub_key}][]"] = sub_value
                        else:
                            params[f"filter[{key}][{sub_key}]"] = sub_value
                elif isinstance(value, list):
                    params[f"filter[{key}][]"] = value
                else:
                    params[f"filter[{key}]"] = value

        data = await self.b2b_client.list_products(params)
        return ProductShortListResponse.model_validate(data)


    async def get_product_detail(self, product_id: UUID) -> Product | None:
        data = await self.b2b_client.get_product(product_id)
        return Product.model_validate(data) if data else None

    async def get_similar_products(
        self,
        product_id: UUID,
        limit: int = 8,
        offset: int = 0
    ) -> ProductShortListResponse:
        params = {"limit": limit, "offset": offset}

        data = await self.b2b_client.get_similar_products(product_id, params)

        items_data = data.get("items", data) if isinstance(data, dict) else data

        mapped_items = []
        for item in items_data:
            if str(item.get("id") == product_id):
                continue

            mapped_items.append(CatalogProductCard(
                id = item["id"],
                name=item.get("title") or item.get("name", ""),
                slug=item.get("slug"),
                min_price=item.get("min_price") or item.get("price", 0),
                old_price=item.get("old_price"),
                has_stock=item.get("has_stock", True),
                images=[{"id": "main", "url": item.get("cover_image"), "is_main": True}]
                       if item.get("cover_image") else [],
                rating=item.get("rating", 0),
                reviews_count=item.get("reviews_count", 0),
            ))

        return ProductShortListResponse(
            items=mapped_items,
            total_count=len(mapped_items),
            limit=limit,
            offset=offset)

    async def get_product_skus(self, product_id: UUID):
        data = await self.b2b_client.get_product_skus(product_id)
        return [SkuShort.model_validate(item) for item in data]

    async def get_product_facets(self, category_id: UUID, dynamic_filters: dict[str, Any]) -> ProductShortListResponse:
        data = await  self.b2b_client.get_facets(category_id, dynamic_filters)
        return ProductShortListResponse.model_validate(data)