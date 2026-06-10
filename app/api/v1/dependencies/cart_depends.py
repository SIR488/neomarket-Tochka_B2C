from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.infrastructure.database import get_db
from app.application.services.cart_service import CartService
from app.api.v1.dependencies.customer_depends import get_current_customer_id_optional
from app.infrastructure.repositories.sku_repository import SKURepository
from app.infrastructure.repositories.cart_repository import CartRepository
from app.infrastructure.b2b_client import B2BClient


async def get_cart_service(db: AsyncSession = Depends(get_db)) -> CartService:
    """Dependency для получения сервиса корзины"""
    repository = CartRepository(db)
    sku_repo = SKURepository(db)
    b2b_client = B2BClient()
    return CartService(repository, sku_repo, b2b_client)


async def resolve_cart(
    customer_id: Optional[UUID] = Depends(get_current_customer_id_optional),
    session_id: Optional[UUID] = Header(alias="X-Session-Id", default=None),
    service: CartService = Depends(get_cart_service)
) -> UUID:
    """
    Резолвит корзину: авторизованную или гостевую.
    Возвращает ID корзины.
    """
    if not customer_id and not session_id:
        raise HTTPException(
            status_code=401, 
            detail="Требуется Authorization или X-Session-Id"
        )

    return await service.resolve_cart(customer_id, session_id)


async def get_cart_service_for_merge(
    db: AsyncSession = Depends(get_db)
) -> CartService:
    """Dependency для слияния корзин (без b2b_client, если не нужен)"""
    repository = CartRepository(db)
    sku_repo = SKURepository(db)
    b2b_client = B2BClient()
    return CartService(repository, sku_repo, b2b_client)


async def merge_guest_cart(
    customer_id: UUID,
    session_id: UUID,
    service: CartService = Depends(get_cart_service_for_merge)
):
    """
    Сливает гостевую корзину в пользовательскую по правилу max(quantity).
    """
    return await service.merge_guest_cart(customer_id, session_id)