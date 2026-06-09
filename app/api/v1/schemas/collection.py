from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel

from app.api.v1.schemas.catalog import CatalogProductCard


class CollectionResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    target_url: Optional[str] = None
    priority: int
    products: List[CatalogProductCard] = []