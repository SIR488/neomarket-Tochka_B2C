from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.favorites_service import FavoritesService
from app.infrastructure.database import get_db
from app.api.v1.dependencies.customer_depends import get_current_customer
from app.api.v1.schemas.favorite import FavoriteRead
from app.infrastructure.repositories.favorites_repository import FavoriteRepository

router = APIRouter()

async def _get_category_service(db: AsyncSession = Depends(get_db)) -> FavoritesService:
    repository = FavoriteRepository(db)
    return FavoritesService(repository)

@router.get("", response_model=list[FavoriteRead], status_code=200, summary="Избранные товары")
async def get_favorites(
    customer_id: UUID = Depends(get_current_customer),
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    service: FavoritesService = Depends(_get_category_service)
):
    favorites = await service.get_favorites(customer_id, limit, offset)
    if not favorites:
        return None

    return favorites

@router.put("/{product_id}", status_code=204, summary="Добавить товар в избранное (Идемпотентно")
async def add_to_favorites(
    product_id: UUID,
    customer_id: UUID = Depends(get_current_customer),
    service: FavoritesService = Depends(_get_category_service)
):
    result = await service.add_to_favorites(customer_id, product_id)
    if not  result:
        raise HTTPException(status_code=404, detail="Товар не найден")

    return None

@router.delete("/{product_id}", status_code=204, summary="Удалить из избранного")
async def delete_favorite(
    product_id: UUID,
    customer_id: UUID = Depends(get_current_customer),
    service: FavoritesService = Depends(_get_category_service)
):
    result = await service.remove_favorite(customer_id, product_id)

    if not result:
        return HTTPException(status_code=404, detail="favorite не найден")

    return None