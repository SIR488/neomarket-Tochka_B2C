from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.infrastructure.database import get_db
from app.application.services.cart_service import CartService
from app.api.v1.dependencies.customer_depends import get_current_customer_id_optional
from app.infrastructure.repositories.sku_repository import SKURepository
from app.infrastructure.repositories.cart_repository import CartRepository

async def get_cart_service(db: AsyncSession = Depends(get_db)) -> CartService:
    repository = CartRepository(db)
    sku_repository = SKURepository(db)
    return CartService(repository, sku_repository)

async def resolve_cart(
    customer_id: Optional[UUID] = Depends(get_current_customer_id_optional),
    session_id: Optional[UUID] = Header(alias="X-Session-Id", default=None),
    service: CartService = Depends(get_cart_service)
) -> UUID:
    """Резолвит корзину: авторизованную или гостевую. Всегда возвращает с eager-loaded отношениями."""
    if not customer_id and not session_id:
        raise HTTPException(status_code=401, detail="Требуется Authorization или X-Session-Id")

    return await service.resolve_cart(customer_id, session_id)

async def merge_guest_cart(
    customer_id: UUID,
    session_id: UUID,
    service: CartService = Depends(get_cart_service)
):
    """
    Сливает гостевую корзину в пользовательскую по правилу max(quantity).
    Не делает commit! Оставляет транзакцию открытой для вызывающего кода.
    """
    return await service.merge_guest_cart(customer_id, session_id)
