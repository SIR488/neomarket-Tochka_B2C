from datetime import datetime
from enum import StrEnum
from typing import Optional, Annotated, Union, Literal, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, Discriminator

class SortOption(StrEnum):
    price_asc = "price_asc"
    price_desc = "price_desc"
    popularity = "popularity"
    new = "new"

class ProductStatus(StrEnum):
    created = "CREATED"
    on_moderated = "ON_MODERATED"
    moderated = "MODERATED"
    blocked = "BLOCKED"

class Image(BaseModel):
    url: HttpUrl
    order: int

class Characteristic(BaseModel):
    id: Optional[UUID] = None
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
    image: Optional[HttpUrl] = None
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
    description: Optional[str] = None
    images: list[Image]
    status: ProductStatus
    characteristics: list[Characteristic]
    skus: list[Sku]

class CategoryNode(BaseModel):
    id: UUID
    name: str
    parent_id: Optional[UUID] = None
    children: list["CategoryNode"] = Field(default_factory=list)

class CategoryTreeResponse(BaseModel):
    items: list[CategoryNode]

class CategoryParent(BaseModel):
    id: UUID
    name: str
    slug: str

class CategorySeo(BaseModel):
    title: str
    description: str
    keywords: list[str] = Field(default_factory=list)

class CategoryMetaTags(BaseModel):
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[HttpUrl] = None
    twitter_card: Optional[str] = None

class CategoryDetailResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    parent: Optional[CategoryParent] = None
    product_count: Optional[int] = None
    seo: CategorySeo
    meta_tags: CategoryMetaTags
    image_url: Optional[HttpUrl] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

class FilterType(StrEnum):
    list = "list"
    range = "range"
    switch = "switch"

class ListFilter(BaseModel):
    slug: str
    name: str
    type: Literal["list"] = "list"
    value: list[str | int | float]

class RangeFilter(BaseModel):
    slug: str
    name: str
    type: Literal["range"] = "range"
    min: float
    max: float

class SwitchFilter(BaseModel):
    slug: str
    name: str
    type: Literal["switch"] = "switch"

class Filter(BaseModel):
    category_id: Optional[UUID] = None
    seller_id: Optional[UUID] = None
    price_min: Optional[int] = Field(None, ge=0)
    price_max: Optional[int] = Field(None, ge=0)
    attributes: Optional[Dict[str, Any]] = Field()

FilterItem = Annotated[
    Union[ListFilter, RangeFilter, SwitchFilter],
    Field(discriminator="type")
]
class FiltersResponse(BaseModel):
    items: list[FilterItem]

class FacetValue(BaseModel):
    value: str
    count: int

class Facet(BaseModel):
    name: str
    values: list[FacetValue]

class FacetsResponse(BaseModel):
    category_id: UUID
    facets: list[Facet]

class BreadcrumbItem(BaseModel):
    id: UUID
    slug: str
    name: str
    url: Optional[str] = None
    level: int
    is_current: bool = False

class BreadcrumbMeta(BaseModel):
    resolved_via: str
    category_id: Optional[UUID] = None
    product_id: Optional[UUID] = None

class BreadcrumbResponse(BaseModel):
    data: list[BreadcrumbItem]
    meta: BreadcrumbMeta
