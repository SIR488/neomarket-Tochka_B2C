from typing import Optional
from uuid import UUID

from app.api.v1.schemas.customer import CustomerResponse
from app.infrastructure.repositories.customer_repository import CustomerRepository

class CustomerService:
    def __init__(self, repository: CustomerRepository):
        self.repository = repository

    async def get_customer_by_id(self, customer_id: UUID) -> Optional[CustomerResponse]:
        customer = await self.repository.get_customer(customer_id)
        if not customer or not customer.is_active:
            return None
        return CustomerResponse.model_validate(customer)

    async def update_current_customer(self, customer_id: UUID, update_data) -> Optional[CustomerResponse]:
        customer = await self.repository.update_partial(customer_id, update_data)
        if not customer:
            return None

        return CustomerResponse.model_validate(customer)

    async def soft_delete_current_customer(self, customer_id: UUID) -> Optional[bool]:
        success = await self.repository.soft_delete(customer_id)
        if not success:
            return None
        return success