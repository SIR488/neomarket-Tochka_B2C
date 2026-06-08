from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.collection_service import CollectionService
from app.infrastructure.database import get_db
from app.infrastructure.repositories.collection_repository import CollectionRepository
from app.api.v1.schemas.collection import CollectionsListResponse

router = APIRouter()


async def _get_collection_service(
    db: AsyncSession = Depends(get_db)
) -> CollectionService:
    repository = CollectionRepository(db)
    return CollectionService(repository)


@router.get("/catalog/collections", response_model=CollectionsListResponse)
async def get_collections(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    service: CollectionService = Depends(_get_collection_service)
):
    """Список активных подборок с товарами"""
    return await service.get_collections(limit, offset)