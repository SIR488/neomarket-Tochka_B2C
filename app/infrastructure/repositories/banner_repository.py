from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import Banner, BannerEvent


class BannerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_banners(self) -> List[Banner]:
        now = datetime.now()
        query = (select(Banner)
                 .where(Banner.is_active == True)
                 .where(
                     (Banner.start_at <= now) | (Banner.start_at == None)
                 )
                 .where(
                     (Banner.end_at >= now) | (Banner.end_at == None)
                 )
                 .order_by(Banner.priority))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_banner_by_id(self, banner_id: UUID) -> Optional[Banner]:
        result = await self.session.execute(
            select(Banner).where(Banner.id == banner_id)
        )
        return result.scalar_one_or_none()

    async def create_events(self, events: List[BannerEvent]) -> int:
        for event in events:
            self.session.add(event)
        await self.session.commit()
        return len(events)