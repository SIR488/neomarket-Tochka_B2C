from uuid import UUID
from datetime import datetime
from sqlmodel import SQLModel


class FavoriteRead(SQLModel):
    customer_id: UUID
    product_id: UUID
    created_at: datetime
