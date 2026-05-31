from pydantic import BaseModel, Field, AliasChoices
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.api.v1.schemas.address import AddressResponse

class OrderItemRequest(BaseModel):
    sku_id: UUID
    quantity: int = Field(ge=1)

class OrderCreateRequest(BaseModel):
    address_id: UUID
    payment_method_id: UUID

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
    subtotal: int = Field(validation_alias=AliasChoices("subtotal", "total_amount"))
    total: int = Field(validation_alias=AliasChoices("total", "total_amount"))
    address: Optional[AddressResponse] = None
    payment_method_id: Optional[UUID] = None
    buyer_id: UUID = Field(validation_alias=AliasChoices("buyer_id", "user_id"))
    created_at: datetime
    updated_at: datetime

class PaginatedOrdersResponse(BaseModel):
    items: List[OrderResponse]
    total_count: int
    limit: int
    offset: int
