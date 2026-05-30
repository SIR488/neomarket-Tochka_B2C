from uuid import UUID
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import Address


class AddressRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, address: Address) -> Address:
        """Создать адрес"""

        self.session.add(address)
        await self.session.commit()
        return address

    async def get_by_id(self, address_id: UUID, customer_id: UUID) -> Optional[Address]:
        """Найти адрес по ID (с проверкой владельца)"""
        query = select(Address).where(
            Address.id == address_id,
            Address.customer_id == customer_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_customer(self, customer_id: UUID) -> List[Address]:
        """Все адреса пользователя"""
        query = select(Address).where(
            Address.customer_id == customer_id
        ).order_by(Address.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, address: Address, update_data: dict) -> Address:
        """Обновить адрес"""

        for key, value in update_data.items():
            if hasattr(address, key) and value is not None:
                setattr(address, key, value)

        await self.session.commit()
        await self.session.refresh(address)
        return address

    async def delete(self, address: Address) -> None:
        """Удалить адрес"""
        await self.session.delete(address)
        await self.session.commit()

    async def reset_default_addresses(self, customer_id: UUID, exclude_address_id: Optional[UUID] = None) -> None:
        """Сбросить флаг is_default у всех адресов пользователя, кроме указанного"""
        query = select(Address).where(
            Address.customer_id == customer_id,
            Address.is_default == True
        )
        
        if exclude_address_id:
            query = query.where(Address.id != exclude_address_id)
        
        result = await self.session.execute(query)
        default_addresses = result.scalars().all()
        
        for address in default_addresses:
            address.is_default = False
            self.session.add(address)
        
        await self.session.commit()