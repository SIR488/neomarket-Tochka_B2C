from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.address_service import AddressService
from app.infrastructure.database import get_db
from app.api.v1.dependencies.customer_depends import get_current_customer
from app.api.v1.schemas.address import AddressRequest, AddressResponse
from app.infrastructure.repositories.address_repository import AddressRepository

router = APIRouter()

async def _get_address_service(db: AsyncSession = Depends(get_db)) -> AddressService:
    repository = AddressRepository(db)
    return AddressService(repository)

@router.get("", response_model=List[AddressResponse], status_code=200)
async def get_addresses(
    customer_id: UUID = Depends(get_current_customer),
    service: AddressService = Depends(_get_address_service)
):
    """Список адресов покупателя"""
    addresses = await service.get_addresses(customer_id)
    return addresses

@router.post("", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    address_data: AddressRequest,
    customer_id: UUID = Depends(get_current_customer),
    service: AddressService = Depends(_get_address_service)
):
    """Добавить новый адрес"""
    return await service.create_address(customer_id, address_data)

@router.patch("/{address_id}", response_model=AddressResponse, status_code=200)
async def update_address(
    address_id: UUID,
    address_data: AddressRequest,
    customer_id: UUID = Depends(get_current_customer),
    service: AddressService = Depends(_get_address_service)
):
    """Изменить адрес"""
    return await service.update_address(address_id, customer_id, address_data)

@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: UUID,
    customer_id: UUID = Depends(get_current_customer),
    service: AddressService = Depends(_get_address_service)
):
    """Удалить адрес"""
    result = await service.delete_address(address_id, customer_id)
    if not result:
        raise HTTPException(status_code=404, detail="Address not found")