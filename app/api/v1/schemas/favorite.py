from uuid import UUID
from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import List
from enum import StrEnum
from pydantic import validator


class SubscriptionEventType(StrEnum):
    BACK_IN_STOCK = "BACK_IN_STOCK"
    PRICE_DROP = "PRICE_DROP"


class FavoriteRead(SQLModel):
    product_id: UUID
    created_at: datetime

class SubscribeRequest(SQLModel):
    events: List[SubscriptionEventType] = Field(default=[SubscriptionEventType.BACK_IN_STOCK, 
                                                         SubscriptionEventType.PRICE_DROP])
    
    @validator('events')
    def not_empty(cls, v):
        if not v:
            raise ValueError('events array must not be empty')
        return v