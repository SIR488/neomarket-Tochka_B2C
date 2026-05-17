from sqlmodel import SQLModel
from uuid import UUID


class CustomerReadShort(SQLModel):
    id: UUID
    name: str

class CustomerResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CustomerUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9\s\-\(\)]+$")

class CustomerLogin(SQLModel):
    name: str
    password: str