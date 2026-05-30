from uuid import UUID
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.models import PaymentMethod


class PaymentMethodRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, payment_method: PaymentMethod) -> PaymentMethod:
        self.session.add(payment_method)
        await self.session.commit()
        await self.session.refresh(payment_method)
        return payment_method

    async def get_by_id(self, method_id: UUID, customer_id: UUID) -> Optional[PaymentMethod]:
        query = select(PaymentMethod).where(
            PaymentMethod.id == method_id,
            PaymentMethod.customer_id == customer_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_customer(self, customer_id: UUID) -> List[PaymentMethod]:
        query = select(PaymentMethod).where(
            PaymentMethod.customer_id == customer_id
        ).order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete(self, payment_method: PaymentMethod) -> None:
        await self.session.delete(payment_method)
        await self.session.commit()

    async def reset_default_methods(self, customer_id: UUID, exclude_method_id: Optional[UUID] = None) -> None:
        query = select(PaymentMethod).where(
            PaymentMethod.customer_id == customer_id,
            PaymentMethod.is_default == True
        )
        
        if exclude_method_id:
            query = query.where(PaymentMethod.id != exclude_method_id)
        
        result = await self.session.execute(query)
        default_methods = result.scalars().all()
        
        for method in default_methods:
            method.is_default = False
        
        await self.session.commit()