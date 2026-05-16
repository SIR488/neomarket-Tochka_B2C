# dependencies/auth.py
from fastapi import HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.infrastructure.models import Customer
from app.api.v1.dependencies.security import get_token_from_cookie, decode_token
from uuid import UUID
from typing import Optional

async def get_current_customer(
    request: Request,
    session: AsyncSession = Depends(get_db)
) -> UUID:
    """
    Dependency: получает текущего авторизованного пользователя.
    При успехе возвращает его ID.
    """
    token = get_token_from_cookie(request)
    if not token:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    customer_id = decode_token(token)
    if not customer_id:
        raise HTTPException(status_code=401, detail="Неверный или просроченный токен")

    customer = await session.get(Customer, customer_id)

    if not customer:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return customer_id

async def get_current_customer_id_optional(
    request: Request
) -> Optional[UUID]:
    """
    Безопасно извлекает ID пользователя из cookie.
    Возвращает None, если токен отсутствует или невалиден (без HTTP 401).
    """
    try:
        token = get_token_from_cookie(request)
        if not token:
            return None
            
        customer_id = decode_token(token)
        return customer_id
    except Exception:
        return None