from uuid import UUID
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routes.products import get_product_service, parse_dynamic_filters
from app.api.v1.routes.categories import get_category_service
from app.application.services.product_service import ProductService
from app.application.services.category_service import CategoryService
from app.application.services.breadcrumb_service import BreadcrumbService
from app.api.v1.schemas.catalog import FacetsResponse, BreadcrumbResponse
from app.infrastructure.database import get_db
from app.infrastructure.repositories.category_repository import CategoryRepository
from app.infrastructure.repositories.product_repository import ProductRepository

router = APIRouter()

async def get_breadcrumb_service(db: AsyncSession = Depends(get_db)) -> CategoryService:
    category_repository = CategoryRepository(db)
    product_repository = ProductRepository(db)
    return BreadcrumbService(product_repo=product_repository, category_repo=category_repository)

@router.get("/facets", response_model=FacetsResponse)
async def get_facets(
    request: Request,
    category_id: UUID = Query(...),
    product_service: ProductService = Depends(get_product_service),
    category_service: CategoryService = Depends(get_category_service)
) -> FacetsResponse:
    category_exists = await category_service.repository.get_by_id(category_id)
    if not category_exists:
        raise HTTPException(status_code=404, detail="Category not found")

    dynamic_filters = parse_dynamic_filters(request)

    facets = await product_service.get_product_facets(category_id, dynamic_filters)
    
    return facets

@router.get("/breadcrumbs", response_model=BreadcrumbResponse)
async def get_breadcrumbs(
    category_id: Optional[UUID] = Query(None),
    product_id: Optional[UUID] = Query(None),
    service: BreadcrumbService = Depends(get_breadcrumb_service)
):
    if category_id and product_id:
        raise HTTPException(status_code=400, detail="Only one of category_id or product_id must be provided")
    if not category_id and not product_id:
        raise HTTPException(status_code=400, detail="Either category_id or product_id must be provided")

    result = await service.get_breadcrumbs(category_id, product_id)
    
    if not result:
        entity = "Product" if product_id else "Category"
        raise HTTPException(status_code=404, detail=f"{entity} not found")
        
    return result