import re
from typing import Annotated, Any
from uuid import UUID
from fastapi import APIRouter, Query, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.repositories.product_repository import ProductRepository
from app.application.services.product_service import ProductService
from app.api.v1.schemas.catalog import (
    Product,
    ProductShortListResponse,
    SkuShort,
    SortOption,
)

router = APIRouter()

async def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    repository = ProductRepository(db)
    return ProductService(repository)

def parse_dynamic_filters(request: Request) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    pattern = re.compile(r'^filter\[([^\]]+)\](?:\[([^\]]+)\])?(?:\[\])?$')

    for key, value in request.query_params.multi_items():
        match = pattern.match(key)
        if not match:
            continue

        main_key = match.group(1)
        sub_key = match.group(2)

        if sub_key:
            if main_key not in filters:
                filters[main_key] = {}
            if isinstance(filters[main_key], dict):
                if sub_key.endswith('[]') or key.endswith('[]'):
                    if sub_key not in filters[main_key]:
                        filters[main_key][sub_key] = []
                    filters[main_key][sub_key].append(value)
                else:
                    filters[main_key][sub_key] = value
        else:  # простой фильтр
            if key.endswith('[]') or isinstance(value, list):
                if main_key not in filters or not isinstance(filters[main_key], list):
                    filters[main_key] = []
                filters[main_key].append(value)
            else:
                filters[main_key] = value

    return filters
@router.get("", response_model=ProductShortListResponse)
async def list_products(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    sort: SortOption | None = Query(None),
    search: Annotated[str | None, Query(min_length=3, max_length=255)] = None,
    service: ProductService = Depends(get_product_service),
):
    dynamic_filters = parse_dynamic_filters(request)
    return await service.get_products(
        limit=limit,
        offset=offset,
        sort=sort,
        search=search,
        filters=dynamic_filters,
    )

@router.get("/{id}", response_model=Product)
async def get_product(
    id: UUID,
    service: ProductService = Depends(get_product_service)
):
    product = await service.get_product_detail(id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/{id}/similar", response_model=ProductShortListResponse)
async def get_similar_products(
    id: UUID,
    limit: Annotated[int, Query(ge=1, le=100)] = 8,
    offset: Annotated[int, Query(ge=0)] = 0,
    service: ProductService = Depends(get_product_service),
):
    return await service.get_similar_products(id, limit, offset)

@router.get("/{product_id}/skus", response_model=list[SkuShort])
async def list_product_skus(
    product_id: UUID,
    service: ProductService = Depends(get_product_service)
) -> list[SkuShort]:
    product = await service.get_product_skus(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return [
        SkuShort(name=s.name, price=s.price, image=s.images[0] if s.images else None) 
        for s in product.skus
    ]
