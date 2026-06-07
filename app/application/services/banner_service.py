from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException

from app.infrastructure.models import Banner, BannerEvent
from app.infrastructure.repositories.banner_repository import BannerRepository
from app.api.v1.schemas.banner import BannerResponse, BannersListResponse, BannerEventItem


class BannerService:
    def __init__(self, repository: BannerRepository):
        self.repository = repository

    async def get_active_banners(self) -> BannersListResponse:
        banners = await self.repository.get_active_banners()
        items = [
            BannerResponse(
                id=b.id,
                title=b.title,
                image_url=b.image_url,
                link=b.link,
                priority=b.priority
            )
            for b in banners
        ]
        return BannersListResponse(items=items, total_count=len(items))

    async def create_events(
        self, 
        events_data: List[BannerEventItem], 
        user_id: Optional[UUID] = None
    ) -> tuple[int, str]:
        if not events_data:
            return -1,"EMPTY_EVENTS"
        
        # Проверяем существование всех баннеров
        for event in events_data:
            banner = await self.repository.get_banner_by_id(event.banner_id)
            if not banner:
                return -1, "BANNER_NOT_FOUND"
        
        events = [
            BannerEvent(
                banner_id=e.banner_id,
                user_id=user_id,
                event=e.event,
                timestamp=e.timestamp
            )
            for e in events_data
        ]
        
        return await self.repository.create_events(events), ""