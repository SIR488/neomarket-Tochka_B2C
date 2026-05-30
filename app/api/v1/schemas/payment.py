from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import StrEnum
from pydantic import BaseModel, Field


class PaymentType(StrEnum):
    CARD = "CARD"
    SBP = "SBP"
    WALLET = "WALLET"

class CardBrand(StrEnum):
    VISA = "VISA"
    MASTERCARD = "MASTERCARD"
    MIR = "MIR"


class PaymentMethodBase(BaseModel):
    type: PaymentType
    card_last4: Optional[str] = Field(default=None, min_length=4, max_length=4)
    card_brand: Optional[CardBrand] = None
    is_default: bool = False


class PaymentMethodCreateRequest(PaymentMethodBase):
    pass


class PaymentMethodResponse(PaymentMethodBase):
    id: UUID
    created_at: datetime