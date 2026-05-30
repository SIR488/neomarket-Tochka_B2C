from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.v1.schemas.order import OrderCreateRequest, OrderResponse
from app.application.services.order_service import OrderService
from app.infrastructure.database import get_db
from app.api.v1.dependencies.customer_depends import get_current_customer
from app.infrastructure.b2b_client import B2BClient

router = APIRouter()

async def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    b2b_client = B2BClient()
    return OrderService(db, b2b_client)

@router.post("", response_model=OrderResponse, status_code=201, summary="Создание заказа (checkout)")
async def create_order(
    request: OrderCreateRequest,
    user_id: UUID = Depends(get_current_customer),
    service: OrderService = Depends(get_order_service)
):
    order = await service.create_order(user_id, request)
    return order
