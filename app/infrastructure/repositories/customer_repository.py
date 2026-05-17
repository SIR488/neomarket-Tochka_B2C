from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.infrastructure.models import Customer

class CustomerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_customer(self, customer_id: UUID) -> Customer:
        query = select(Customer).where(Customer.id == customer_id)
        result = await self.session.execute(query)

        return result.scalar_one_or_none()

    async def update_partial(self, customer_id: UUID, data: dict) -> Customer:
        query = (
            update(Customer)
            .where(Customer.id == customer_id)
            .values(**data)
            .returning(Customer)
        )
        result = await self.session.execute(query)
        await self.session.commit()

        return result.scalar_one_or_none()

    async def soft_delete(self, customer_id: UUID) -> bool:
        query = (
            update(Customer)
            .where(Customer.id == customer_id)
            .values(is_active=False)
        )
        result = await self.session.execute(query)
        await self.session.commit()

        return result.rowcount > 0