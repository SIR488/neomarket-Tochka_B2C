from uuid import UUID
from fastapi import APIRouter, Depends, Request, Query, HTTPException

from app.api.v1.routes.products import get_product_service, parse_dynamic_filters
from app.api.v1.routes.categories import get_category_service
from app.application.services.product_service import ProductService
from app.application.services.category_service import CategoryService
from app.api.v1.schemas.catalog import FacetsResponse

router = APIRouter()

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