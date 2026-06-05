from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.error import Error
from app.infrastructure.database import get_db
from app.infrastructure.repositories.category_repository import CategoryRepository
from app.application.services.category_service import CategoryService
from app.api.v1.schemas.catalog import CategoryTreeResponse, CategoryDetailResponse, FiltersResponse

router = APIRouter()

async def get_category_service(db: AsyncSession = Depends(get_db)) -> CategoryService:
    repository = CategoryRepository(db)
    return CategoryService(repository)

@router.get("", response_model=CategoryTreeResponse, summary="Получить дерево категорий")
async def get_categories(
    service: CategoryService = Depends(get_category_service)
) -> CategoryTreeResponse:
    tree = await service.get_category_tree()

    if not tree:
        raise HTTPException(
            status_code=422,
            detail=Error(
                code="ORPHAN_NODE",
                message="Обнаружены категории с несуществующими родителями (broken hierarchy)"
            ).model_dump()
        )
    return CategoryTreeResponse(items=tree)

@router.get("/{id}", response_model=CategoryDetailResponse, summary="Детальная информация о категории")
async def get_category(
    id: UUID,
    include_product_count: bool = False,
    lang: str = "ru",
    service: CategoryService = Depends(get_category_service)
) -> CategoryDetailResponse:
    category = await service.get_category_detail(
        id, 
        include_product_count=include_product_count,
        lang=lang
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.get("/{id}/filters", response_model=FiltersResponse, summary="Список фильтров категории")
async def get_category_filters(
    id: UUID,
    service: CategoryService = Depends(get_category_service)
) -> FiltersResponse:
    filters = await service.get_category_filters(id)
    
    if filters is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Category with id {id} not found"
        )
        
    return filters
