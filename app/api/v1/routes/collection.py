from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.collection_service import CollectionService
from app.api.v1.dependencies.collection_depends import get_collection_service
from app.api.v1.schemas.collection import CollectionResponse

router = APIRouter()


@router.get("/catalog/collections", response_model=list[CollectionResponse])
async def get_collections(
    service: CollectionService = Depends(get_collection_service)
):
    """Список активных подборок с товарами"""
    return await service.get_collections()