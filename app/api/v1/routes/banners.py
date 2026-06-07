from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.banner_service import BannerService
from app.infrastructure.database import get_db
from app.api.v1.dependencies.customer_depends import get_current_customer_id_optional
from app.api.v1.schemas.banner import BannersListResponse, BannerEventRequest, BannerEventResponse

router = APIRouter()


async def _get_banner_service(db: AsyncSession = Depends(get_db)) -> BannerService:
    from app.infrastructure.repositories.banner_repository import BannerRepository
    repository = BannerRepository(db)
    return BannerService(repository)


@router.get("/home/banners", response_model=BannersListResponse, status_code=200)
async def get_banners(
    service: BannerService = Depends(_get_banner_service)
):
    """Получить список активных баннеров для главной страницы"""
    return await service.get_active_banners()


@router.post("/banner-events", response_model=BannerEventResponse, status_code=200)
async def create_banner_events(
    request: BannerEventRequest,
    user_id: Optional[UUID] = Depends(get_current_customer_id_optional),
    service: BannerService = Depends(_get_banner_service)
):
    """Отправить события показов/кликов для аналитики CTR"""
    accepted, error = await service.create_events(request.events, user_id)
    if accepted==-1:
        raise HTTPException(status_code=400, detail=error)
    return BannerEventResponse(
        accepted=accepted,
        message=f"Accepted {accepted} events"
    )