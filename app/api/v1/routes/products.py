import re
from typing import Annotated, Any
from uuid import UUID
from fastapi import APIRouter, Query, Request, HTTPException

from app.api.v1.schemas.catalog import (
    Product,
    ProductShortListResponse,
    Sku,
    SkuShort,
    SortOption,
)

router = APIRouter()

def parse_dynamic_filters(request: Request) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    pattern = re.compile(r'^filters\[([^\]]+)\](?:\[\])?$')
    
    for key, value in request.query_params.multi_items():
        match = pattern.match(key)
        if match:
            filter_name = match.group(1)
            if filter_name not in filters:
                filters[filter_name] = value
            else:
                if not isinstance(filters[filter_name], list):
                    filters[filter_name] = [filters[filter_name]]
                filters[filter_name].append(value)
    return filters

@router.get("", response_model=ProductShortListResponse)
async def list_products(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    category_id: UUID | None = None,
    sort: SortOption | None = None,
    search: Annotated[str | None, Query(min_length=3, max_length=255)] = None,
) -> ProductShortListResponse:
    dynamic_filters = parse_dynamic_filters(request)
    # TODO: Внедрить Use Case
    return ProductShortListResponse(
        total_count=0,
        limit=limit,
        offset=offset,
        items=[]
    )

@router.get("/{product_id}/skus", response_model=list[SkuShort])
async def list_product_skus(product_id: UUID) -> list[SkuShort]:
    return []

@router.get("/{product_id}/skus/{sku_id}", response_model=Sku)
async def get_product_sku(product_id: UUID, sku_id: UUID) -> Sku:
    raise HTTPException(status_code=404, detail="Not implemented")

@router.get("/{id}/similar", response_model=ProductShortListResponse)
async def get_similar_products(
    id: UUID,
    category: UUID,
    limit: Annotated[int, Query(ge=1, le=100)] = 8,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProductShortListResponse:
    return ProductShortListResponse(total_count=0, limit=limit, offset=offset, items=[])

@router.get("/{id}", response_model=Product)
async def get_product(id: UUID) -> Product:
    raise HTTPException(status_code=404, detail="Product not found")
