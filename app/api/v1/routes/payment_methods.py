from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.payment_service import PaymentMethodService
from app.infrastructure.database import get_db
from app.api.v1.dependencies.customer_depends import get_current_customer
from app.api.v1.schemas.payment import PaymentMethodCreateRequest, PaymentMethodResponse
from app.infrastructure.repositories.payment_repository import PaymentMethodRepository

router = APIRouter()

async def _get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentMethodService:
    repository = PaymentMethodRepository(db)
    return PaymentMethodService(repository)


@router.get("", response_model=List[PaymentMethodResponse], status_code=200)
async def get_payment_methods(
    customer_id: UUID = Depends(get_current_customer),
    service: PaymentMethodService = Depends(_get_payment_service)
):
    methods = await service.get_payment_methods(customer_id)
    return methods


@router.post("", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    method_data: PaymentMethodCreateRequest,
    customer_id: UUID = Depends(get_current_customer),
    service: PaymentMethodService = Depends(_get_payment_service)
):
    return await service.create_payment_method(customer_id, method_data)


@router.delete("/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_method(
    method_id: UUID,
    customer_id: UUID = Depends(get_current_customer),
    service: PaymentMethodService = Depends(_get_payment_service)
):
    result = await service.delete_payment_method(method_id, customer_id)
    if not result:
        raise HTTPException(status_code=404, detail="Payment method not found")