from uuid import UUID
from typing import List
from fastapi import HTTPException

from app.infrastructure.repositories.address_repository import AddressRepository
from app.infrastructure.models import Address
from app.api.v1.schemas.address import AddressRequest


class AddressService:
    def __init__(self, repository: AddressRepository):
        self.repository = repository

    async def get_addresses(self, customer_id: UUID) -> List[Address]:
        """Получить все адреса пользователя"""
        return await self.repository.get_all_by_customer(customer_id)

    async def create_address(
        self, 
        customer_id: UUID, 
        address_data: AddressRequest
    ) -> Address:
        """Создать новый адрес"""
        if address_data.is_default:
            await self.repository.reset_default_addresses(customer_id)
        
        address = Address(
            customer_id=customer_id,
            country=address_data.country,
            region=address_data.region,
            city=address_data.city,
            street=address_data.street,
            building=address_data.building,
            apartment=address_data.apartment,
            postal_code=address_data.postal_code,
            recipient_name=address_data.recipient_name,
            recipient_phone=address_data.recipient_phone,
            comment=address_data.comment,
            is_default=address_data.is_default
        )
        
        return await self.repository.create(address)

    async def update_address(
        self,
        address_id: UUID,
        customer_id: UUID,
        update_data: AddressRequest
    ) -> Address:
        """Обновить существующий адрес"""
        address = await self.repository.get_by_id(address_id, customer_id)
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if update_dict.get("is_default") is True and not address.is_default:
            await self.repository.reset_default_addresses(customer_id, exclude_address_id=address_id)
        
        return await self.repository.update(address, update_dict)

    async def delete_address(
        self,
        address_id: UUID,
        customer_id: UUID
    ) -> bool:
        """Удалить адрес"""
        address = await self.repository.get_by_id(address_id, customer_id)
        if not address:
            return False
        
        await self.repository.delete(address)
        return True