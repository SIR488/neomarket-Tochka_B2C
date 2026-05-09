# dependencies/auth.py
from fastapi import HTTPException, Depends, Request
from sqlmodel import Session
from app.infrastructure.database import get_db
from app.infrastructure.models import Customer
from app.api.v1.dependencies.security import get_token_from_cookie, decode_token
from uuid import UUID

def get_current_customer(
    request: Request,
    session: Session = Depends(get_db)
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

    customer = session.get(Customer, customer_id)

    if not customer:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return customer_id