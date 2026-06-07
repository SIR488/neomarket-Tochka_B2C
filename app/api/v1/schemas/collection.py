from uuid import UUID
from typing import List, Optional, Any
from pydantic import BaseModel


class CollectionResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    target_url: Optional[str] = None
    priority: int


class CollectionsListResponse(BaseModel):
    items: List[CollectionResponse]
    total_count: int
    limit: int
    offset: int


class CollectionProductsResponse(BaseModel):
    collection_id: UUID
    title: str
    items: List[Any]  # ProductShort из catalog
    unavailable_ids: List[UUID] = []
    total_count: int
    limit: int
    offset: int