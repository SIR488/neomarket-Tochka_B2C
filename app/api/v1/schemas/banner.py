from uuid import UUID
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class BannerResponse(BaseModel):
    id: UUID
    image_url: str
    link: str
    title: Optional[str] = None
    ordering: Optional[int] = None
    active_from: Optional[datetime] = None
    active_to: Optional[datetime] = None


class BannerEventItem(BaseModel):
    banner_id: UUID
    event: str = Field(..., pattern="^(impression|click)$")
    timestamp: datetime


class BannerEventRequest(BaseModel):
    events: List[BannerEventItem]


class BannerEventResponse(BaseModel):
    accepted: int
    message: str