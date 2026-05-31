from fastapi import APIRouter, Depends, HTTPException, Response, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID

from app.infrastructure.database import get_db
from app.infrastructure.models import Customer
from app.api.v1.schemas.customer import (CustomerRegister, CustomerLogin, 
                                         TokenResponse, RefreshRequest)
from app.api.v1.dependencies.security import (
    hash_password,
    verify_password,
    create_auth_tokens,
    decode_token
)
from app.api.v1.dependencies.cart_depends import merge_guest_cart

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register_customer(
    customer: CustomerRegister,
    session: AsyncSession = Depends(get_db)
):
    """Регистрация покупателя. Возвращает пару токенов (access + refresh)."""
    statement = select(Customer).where(Customer.email == customer.email)
    result = await session.execute(statement)
    existing_customer = result.scalar_one_or_none()
    if existing_customer:
        raise HTTPException(status_code=409, detail="Пользователь с такой почтой уже существует")
    
    db_customer = Customer(
        email=customer.email,
        first_name=customer.first_name,
        last_name=customer.last_name,
        date_of_birth=customer.date_of_birth,
        password_hash=hash_password(customer.password)
    )
    
    session.add(db_customer)
    await session.commit()
    await session.refresh(db_customer)
    
    tokens = create_auth_tokens(db_customer.id)
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login_customer(
    customer: CustomerLogin,
    response: Response,
    session: AsyncSession = Depends(get_db),
    session_id: Optional[UUID] = Header(alias="X-Session-Id", default=None)
):
    """Вход покупателя. Возвращает пару токенов (access + refresh)."""
    statement = select(Customer).where(Customer.email == customer.email)
    result = await session.execute(statement)
    existing_customer = result.scalar_one_or_none()
    
    if not existing_customer or not verify_password(customer.password, existing_customer.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    if session_id:
        await merge_guest_cart(existing_customer.id, session_id)
    
    await session.commit()
    
    tokens = create_auth_tokens(existing_customer.id)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshRequest,
    session: AsyncSession = Depends(get_db)
):
    """Обновление access-токена по refresh-токену."""
    customer_id = decode_token(refresh_data.refresh_token, expected_type="refresh")
    if customer_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    customer = await session.get(Customer, customer_id)
    if not customer or not customer.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return create_auth_tokens(customer_id)


@router.post("/logout", status_code=204)
async def logout_customer(response: Response):
    """
    Выход из аккаунта.
    Удаляет httpOnly cookie (если используется).
    Refresh-токен остаётся валидным до истечения срока (stateless JWT).
    """
    return