from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.collection_service import CollectionService
from app.infrastructure.database import get_db
from app.infrastructure.repositories.collection_repository import CollectionRepository
from app.api.v1.schemas.collection import (
    CollectionsListResponse, CollectionProductsResponse
)

router = APIRouter()


async def _get_collection_service(
    db: AsyncSession = Depends(get_db)
) -> CollectionService:
    repository = CollectionRepository(db)
    return CollectionService(repository)


@router.get("/main/collections", response_model=CollectionsListResponse)
async def get_collections(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    service: CollectionService = Depends(_get_collection_service)
):
    """Список активных подборок (без товаров)"""
    return await service.get_collections(limit, offset)


@router.get("/collections/{collection_id}/products", response_model=CollectionProductsResponse)
async def get_collection_products(
    collection_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: CollectionService = Depends(_get_collection_service)
):
    """Товары подборки (обогащённые из локальной БД)"""
    return await service.get_collection_products(collection_id, limit, offset)