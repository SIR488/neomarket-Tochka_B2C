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
    id: UUID
    url: str
    alt: str
    ordering: int
    is_main: bool

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
    price: int
    old_price: int
    available_quantity: int
    attributes: list[Characteristic]
    images: list[Image] = Field(default_factory=list)

class CategoryNode(BaseModel):
    id: UUID
    name: str
    parent_id: Optional[UUID] = None
    level: int
    path: list[str]
    children: list["CategoryNode"] = Field(default_factory=list)

class CategoryNodeShort(BaseModel):
    id: UUID
    name: str
    parent_id: Optional[UUID] = None
    level: int
    path: list[str]

class SellerShort(BaseModel):
    id: UUID
    display_name: str

class ProductShort(BaseModel):
    id: UUID
    name: str
    slug: str
    category: CategoryNodeShort
    min_price: int
    old_price: int
    has_stock: bool
    rating: int
    reviews_count: int
    images: list[Image]
    seller: SellerShort

class ProductShortListResponse(BaseModel):
    items: list[ProductShort]
    total_count: int
    limit: int
    offset: int

class Product(BaseModel):
    id: UUID
    name: str
    slug: str
    category: CategoryNodeShort
    min_price: int
    old_price: int
    has_stock: bool
    rating: int
    reviews_count: int
    images: list[Image]
    seller: SellerShort
    description: Optional[str] = None
    attributes: list[Characteristic]
    skus: list[Sku]

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
    image_url: Optional[str] = None
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


class ImageRef(BaseModel):
    id: UUID
    url: str
    alt: Optional[str] = None
    ordering: int = 0
    is_main: bool = False

class CatalogProductCard(BaseModel):
    id: UUID
    name: str
    min_price: int
    has_stock: bool
    images: list[ImageRef]
    slug: Optional[str] = None
    old_price: Optional[int] = None
    rating: Optional[float] = None
    reviews_count: int = 0

class PaginatedCatalogProducts(BaseModel):
    items: list[CatalogProductCard]
    total_count: int
    limit: int
    offset: int