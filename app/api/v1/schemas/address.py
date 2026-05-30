from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re

class AddressBase(BaseModel):
    country: str = Field(min_length=1, max_length=100)
    region: Optional[str] = Field(default=None, max_length=200)
    city: str = Field(min_length=1, max_length=200)
    street: str = Field(min_length=1, max_length=200)
    building: str = Field(min_length=1, max_length=50)
    apartment: Optional[str] = Field(default=None, max_length=50)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    recipient_name: Optional[str] = Field(default=None, max_length=200)
    recipient_phone: Optional[str] = Field(default=None, max_length=20)
    comment: Optional[str] = Field(default=None, max_length=500)
    is_default: bool = False
'''
    @field_validator('recipient_phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        pattern = r'^\+?[0-9]{10,15}$'
        if not re.match(pattern, v):
            raise ValueError('Phone must be in international format (+71234567890)')
        return v'''

class AddressRequest(AddressBase):
    pass

class AddressResponse(AddressBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None