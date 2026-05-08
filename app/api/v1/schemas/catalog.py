from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl

class SortOption(StrEnum):
    rating = "rating"
    popularity = "popularity"
    price_asc = "price_asc"
    price_desc = "price_desc"
    date_desc = "date_desc"
    discount_desc = "discount_desc"

class ProductStatus(StrEnum):
    created = "CREATED"
    on_moderated = "ON_MODERATED"
    moderated = "MODERATED"
    blocked = "BLOCKED"

class Image(BaseModel):
    url: HttpUrl
    order: int

class Characteristic(BaseModel):
    id: UUID | None = None
    name: str
    value: str

class SkuShort(BaseModel):
    name: str
    price: float
    image: Image

class Sku(BaseModel):
    id: UUID
    name: str
    price: float
    quantity: int
    characteristics: list[Characteristic]
    images: list[Image] = Field(default_factory=list)

class ProductShort(BaseModel):
    id: UUID
    title: str
    image: HttpUrl
    price: float
    in_stock: bool
    is_in_cart: bool

class ProductShortListResponse(BaseModel):
    total_count: int
    limit: int
    offset: int
    items: list[ProductShort]

class Product(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str
    images: list[Image]
    status: ProductStatus
    characteristics: list[Characteristic]
    skus: list[Sku]
