from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class OrderItemRequest(BaseModel):
    sku_id: UUID
    quantity: int = Field(ge=1)

class OrderCreateRequest(BaseModel):
    idempotency_key: UUID
    items: List[OrderItemRequest]
    delivery_address: Optional[str] = None

class OrderItemResponse(BaseModel):
    id: UUID
    sku_id: UUID
    product_id: UUID
    product_title: str
    sku_name: str
    quantity: int
    unit_price: int
    line_total: int

class OrderResponse(BaseModel):
    id: UUID
    status: str
    items: List[OrderItemResponse]
    total_amount: int
    delivery_address: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class OrderShortResponse(BaseModel):
    id: UUID
    status: str
    total_amount: int
    items_count: int
    created_at: datetime
    updated_at: datetime

class PaginatedOrdersResponse(BaseModel):
    items: List[OrderShortResponse]
    total_count: int
    limit: int
    offset: int
