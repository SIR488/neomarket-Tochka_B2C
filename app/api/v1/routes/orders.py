from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.v1.schemas.order import OrderCreateRequest, OrderResponse, PaginatedOrdersResponse
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

@router.get("", response_model=PaginatedOrdersResponse, summary="Получение списка заказов")
async def get_orders(
    limit: int = 10,
    offset: int = 0,
    user_id: UUID = Depends(get_current_customer),
    service: OrderService = Depends(get_order_service)
):
    """
    Возвращает список заказов текущего покупателя с пагинацией.
    """
    return await service.get_orders(user_id=user_id, limit=limit, offset=offset)

@router.get("/{order_id}", response_model=OrderResponse, summary="Получение информации о заказе")
async def get_order(
    order_id: UUID,
    user_id: UUID = Depends(get_current_customer),
    service: OrderService = Depends(get_order_service)
):
    """
    Возвращает детали заказа.
    При попытке получить чужой заказ возвращает 404 (IDOR защита).
    """
    return await service.get_order_by_id(user_id=user_id, order_id=order_id)

@router.post("/{order_id}/cancel", response_model=OrderResponse, summary="Отмена заказа")
async def cancel_order(
    order_id: UUID,
    user_id: UUID = Depends(get_current_customer),
    service: OrderService = Depends(get_order_service)
):
    """
    Отменяет заказ.
    """
    return await service.cancel_order(user_id=user_id, order_id=order_id)

from pydantic import BaseModel

class OrderStatusUpdate(BaseModel):
    status: str

@router.post("/{order_id}/status", response_model=OrderResponse, summary="Смена статуса заказа (служебный)")
async def update_order_status(
    order_id: UUID,
    payload: OrderStatusUpdate,
    service: OrderService = Depends(get_order_service)
):
    """
    Служебный эндпоинт для смены статуса заказа.
    При переводе в статус DELIVERED отправляет запрос fulfill в B2B.
    """
    return await service.update_order_status(order_id=order_id, new_status=payload.status)
