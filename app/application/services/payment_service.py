from uuid import UUID
from typing import List
from fastapi import HTTPException

from app.infrastructure.repositories.payment_repository import PaymentMethodRepository
from app.infrastructure.models import PaymentMethod
from app.api.v1.schemas.payment import PaymentMethodCreateRequest, PaymentType


class PaymentMethodService:
    def __init__(self, repository: PaymentMethodRepository):
        self.repository = repository

    async def get_payment_methods(self, customer_id: UUID) -> List[PaymentMethod]:
        return await self.repository.get_all_by_customer(customer_id)

    async def create_payment_method(
        self, 
        customer_id: UUID, 
        method_data: PaymentMethodCreateRequest
    ) -> PaymentMethod:
        if method_data.type == PaymentType.CARD:
            if not method_data.card_last4:
                raise HTTPException(
                    status_code=400, 
                    detail="card_last4 is required for CARD type"
                )
            if not method_data.card_brand:
                raise HTTPException(
                    status_code=400, 
                    detail="card_brand is required for CARD type"
                )
        
        if method_data.is_default:
            await self.repository.reset_default_methods(customer_id)
        
        payment_method = PaymentMethod(
            customer_id=customer_id,
            type=method_data.type,
            card_last4=method_data.card_last4,
            card_brand=method_data.card_brand,
            is_default=method_data.is_default
        )
        
        return await self.repository.create(payment_method)

    async def delete_payment_method(
        self,
        method_id: UUID,
        customer_id: UUID
    ) -> bool:
        payment_method = await self.repository.get_by_id(method_id, customer_id)
        if not payment_method:
            return False
        
        was_default = payment_method.is_default
        
        await self.repository.delete(payment_method)
        
        if was_default:
            remaining = await self.repository.get_all_by_customer(customer_id)
            if remaining:
                new_default = remaining[0]
                new_default.is_default = True
                await self.repository.reset_default_methods(customer_id, exclude_method_id=new_default.id)
        
        return True