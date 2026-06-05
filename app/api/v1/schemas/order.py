from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import List, Optional, Any
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
    sku_id: UUID
    product_id: UUID
    name: str
    sku_code: Optional[str] = None
    quantity: int
    unit_price: int
    line_total: int
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def populate_name(cls, data: Any) -> Any:
        if hasattr(data, 'product_title') and hasattr(data, 'sku_name'):
            setattr(data, 'name', f"{data.product_title} - {data.sku_name}")
        elif isinstance(data, dict):
            data['name'] = f"{data.get('product_title', '')} - {data.get('sku_name', '')}"
        return data

class OrderResponse(BaseModel):
    id: UUID
    number: Optional[str] = None
    buyer_id: UUID
    status: str
    status_history: Optional[List[dict]] = None
    items: List[OrderItemResponse]
    subtotal: int
    delivery_cost: int = 0
    total: int
    address: Optional[AddressResponse] = None
    payment_method: Optional[Any] = None
    comment: Optional[str] = None
    cancel_reason: Optional[str] = None
    created_at: datetime
    paid_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if hasattr(data, 'total_amount'):
            setattr(data, 'subtotal', data.total_amount)
            setattr(data, 'total', data.total_amount)
        if hasattr(data, 'user_id'):
            setattr(data, 'buyer_id', data.user_id)
        elif isinstance(data, dict):
            if 'total_amount' in data:
                data['subtotal'] = data['total_amount']
                data['total'] = data['total_amount']
            if 'user_id' in data:
                data['buyer_id'] = data['user_id']
        return data

class PaginatedOrdersResponse(BaseModel):
    items: List[OrderResponse]
    total_count: int
    limit: int
    offset: int
