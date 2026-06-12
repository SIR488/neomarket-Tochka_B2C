from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from enum import StrEnum
from app.api.v1.schemas.catalog import ImageRef

class CartItemAddRequest(BaseModel):
    sku_id: UUID
    quantity: int = Field(ge=1)

class CartValidationIssueType(StrEnum):
    PRICE_CHANGED = "PRICE_CHANGED"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    QUANTITY_REDUCED = "QUANTITY_REDUCED"
    PRODUCT_BLOCKED = "PRODUCT_BLOCKED"
    PRODUCT_DELETED = "PRODUCT_DELETED"

class CartItem(BaseModel):
    sku_id: UUID
    product_id: UUID
    name: str
    sku_code: Optional[str] = None
    quantity: int = Field(ge=1)
    unit_price: int
    unit_price_at_add: Optional[int] = None
    line_total: int
    available_quantity: int
    is_available: bool
    image: Optional[ImageRef] = None
    unavailable_reason: Optional[str] = None

class CartResponse(BaseModel):
    id: Optional[UUID] = None
    items: List[CartItem]
    items_count: int
    subtotal: int
    is_valid: bool

class CartValidationIssue(BaseModel):
    sku_id: UUID
    type: CartValidationIssueType
    message: str
    old_value: Optional[int | str] = None
    new_value: Optional[int | str] = None

class CartValidationResponse(BaseModel):
    is_valid: bool
    cart: CartResponse
    issues: List[CartValidationIssue] = []