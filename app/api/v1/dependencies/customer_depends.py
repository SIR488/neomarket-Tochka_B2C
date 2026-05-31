from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.infrastructure.models import Customer
from app.api.v1.dependencies.security import decode_token
from uuid import UUID
from typing import Optional

bearer_scheme = HTTPBearer()
optional_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db)
) -> UUID:
    """
    Dependency: получает текущего авторизованного пользователя из Bearer токена.
    При успехе возвращает customer_id.
    """
    customer_id = decode_token(credentials.credentials, expected_type="access")
    if not customer_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    customer = await session.get(Customer, customer_id)
    if not customer or not customer.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return customer_id


async def get_current_customer_id_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer_scheme),
    session: AsyncSession = Depends(get_db)
) -> Optional[UUID]:
    """
    Безопасно извлекает ID пользователя (без HTTP 401).
    Возвращает None, если токен отсутствует или невалиден.
    """
    if not credentials:
        return None
    
    customer_id = decode_token(credentials.credentials, expected_type="access")
    if not customer_id:
        return None
    
    customer = await session.get(Customer, customer_id)
    if not customer or not customer.is_active:
        return None
    
    return customer_id