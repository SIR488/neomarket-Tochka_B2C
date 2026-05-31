from sqlmodel import SQLModel
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

class CustomerRegister(SQLModel):
    email: str
    first_name: str
    last_name: str
    date_of_birth: date
    password: str

class CustomerReadShort(SQLModel):
    id: UUID
    email: str

class CustomerResponse(BaseModel):
    id: UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class CustomerUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9\s\-\(\)]+$")

class CustomerLogin(SQLModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    user_id: UUID
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int

    class Config:
        from_attributes = True

class RefreshRequest(BaseModel):
    refresh_token: str