import re
from typing import Annotated, Any
from uuid import UUID
from fastapi import APIRouter, Query, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.api.v1.dependencies.customer_depends import get_current_customer
from app.infrastructure.repositories.product_repository import ProductRepository
from app.application.services.product_service import ProductService
from app.api.v1.schemas.catalog import (
    Product,
    ProductShortListResponse,
    SkuShort,
    SortOption,
    Sku
)

router = APIRouter()

async def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    repository = ProductRepository(db)
    return ProductService(repository)

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

@router.get("", response_model=ProductShortListResponse, summary="Получить список товаров")
async def list_products(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    category_id: UUID | None = Query(None, description="Фильтр по категории"),
    sort: SortOption | None = Query(None, description="Сортировка"),
    search: Annotated[str | None, Query(min_length=3, max_length=255)] = None,
    service: ProductService = Depends(get_product_service)
) -> ProductShortListResponse:
    dynamic_filters = parse_dynamic_filters(request)
    return await service.get_products(
        limit=limit, offset=offset, category_id=category_id,
        sort=sort, search=search, filters=dynamic_filters
    )

@router.get("/{id}", response_model=Product, summary="Получить полную карточку товара")
async def get_product(
    id: UUID, 
    service: ProductService = Depends(get_product_service)
) -> Product:
    product = await service.get_product_detail(id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/{id}/similar", response_model=ProductShortListResponse, summary="Получить похожие товары")
async def get_similar_products(
    id: UUID,
    category: UUID = Query(..., description="Обязательный ID категории"),
    limit: Annotated[int, Query(ge=1, le=100)] = 8,
    offset: Annotated[int, Query(ge=0)] = 0,
    service: ProductService = Depends(get_product_service)
) -> ProductShortListResponse:
    return await service.get_products(
        limit=limit, offset=offset, category_id=category
    )

@router.get("/{product_id}/skus", response_model=list[SkuShort], summary="Получить список SKU")
async def list_product_skus(
    product_id: UUID,
    service: ProductService = Depends(get_product_service)
) -> list[SkuShort]:
    product = await service.get_product_detail(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return [
        SkuShort(name=s.name, price=s.price, image=s.images[0] if s.images else None) 
        for s in product.skus
    ]

@router.get("/{product_id}/skus/{sku_id}", response_model=Sku, summary="Информация о SKU")
async def get_sku_info(
    product_id: UUID,
    sku_id: UUID,
    service: ProductService = Depends(get_product_service)
):
    try:
        sku_detail = await service.get_sku_detail(product_id, sku_id)
        
        if sku_detail is None:
            raise HTTPException(status_code=404, detail="SKU or Product not found")
            
        return sku_detail

    except PermissionError:
        raise HTTPException(
            status_code=403, 
            detail="Access denied: product is not moderated"
        )
    except Exception as e:
        raise e
