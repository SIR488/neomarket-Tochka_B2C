from uuid import UUID
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class BannerResponse(BaseModel):
    id: UUID
    title: str
    image_url: str
    link: str
    priority: int


class BannersListResponse(BaseModel):
    items: List[BannerResponse]
    total_count: int


class BannerEventItem(BaseModel):
    banner_id: UUID
    event: str = Field(..., pattern="^(impression|click)$")
    timestamp: datetime


class BannerEventRequest(BaseModel):
    events: List[BannerEventItem]


class BannerEventResponse(BaseModel):
    accepted: int
    message: str