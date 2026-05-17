from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.customer_depends import get_current_customer_id_optional
from app.api.v1.schemas.customer import CustomerResponse, CustomerUpdateRequest
from app.application.services.customer_service import CustomerService
from app.infrastructure.database import get_db
from app.infrastructure.repositories.customer_repository import CustomerRepository

router = APIRouter()

async def get_breadcrumb_service(db: AsyncSession = Depends(get_db)) -> CustomerService:
    repository = CustomerRepository(db)
    return CustomerService(repository)

@router.get("", response_model=CustomerResponse, status_code=200, summary="Профиль текущего пользователя")
async def get_customer(
        customer_id: Optional[UUID] = Depends(get_current_customer_id_optional),
        service: CustomerService = Depends(get_breadcrumb_service)
):
    if not customer_id:
        raise HTTPException(status_code=401, detail="not authorized")

    response = await service.get_customer_by_id(customer_id)
    if not response:
        raise HTTPException(status_code=404, detail="Покупатель не найден")

    return response

@router.patch("", response_model=CustomerResponse, status_code=200, summary="Частичное обновление профиля")
async def update_current_buyer(
    request: CustomerUpdateRequest,
    customer_id: Optional[UUID] = Depends(get_current_customer_id_optional),
    service: CustomerService = Depends(get_breadcrumb_service),
):
    if not customer_id:
        raise HTTPException(status_code=401, detail="not authorized")

    update_data = request.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    customer = await service.update_current_customer(customer_id, update_data)
    if not customer:
        raise HTTPException(status_code=404, detail="Покупатель не найден")

    return customer


@router.delete("", status_code=204, summary="Soft-delete профиля")
async def delete_current_buyer(
    customer_id: Optional[UUID] = Depends(get_current_customer_id_optional),
    service: CustomerService = Depends(get_breadcrumb_service),
):
    if not customer_id:
        raise HTTPException(status_code=401, detail="not authorized")

    success = await service.soft_delete_current_customer(customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Покупатель не найден")

    return None
