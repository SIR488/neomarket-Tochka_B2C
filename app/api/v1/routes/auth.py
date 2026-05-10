from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.database import get_db
from app.infrastructure.models import Customer
from app.api.v1.schemas.customer import CustomerRead, CustomerLogin
from app.api.v1.dependencies.security import hash_password, set_auth_cookie, verify_password, delete_auth_cookie

router = APIRouter()

@router.post("/register", response_model=CustomerRead)
async def register_customer(customer: CustomerLogin, response: Response, session: AsyncSession = Depends(get_db)):  # <- AsyncSession
    """Регистрация пользователя."""
    statement = select(Customer).where(Customer.name == customer.name)
    result = await session.execute(statement)
    existing_customer = result.scalar_one_or_none()
    if existing_customer:
        raise HTTPException(status_code=409, detail="Пользователь с таким именем уже существует")
    
    db_customer = Customer(
        name=customer.name,
        password_hash=hash_password(customer.password),
    )
    session.add(db_customer)
    await session.commit()
    await session.refresh(db_customer)

    set_auth_cookie(response, customer_id=db_customer.id)
    return db_customer

@router.post("/login", response_model=CustomerRead)
async def login_customer(customer: CustomerLogin, response: Response, session: AsyncSession = Depends(get_db)):  # <- AsyncSession
    """Авторизация пользователя."""
    statement = select(Customer).where(Customer.name == customer.name)
    result = await session.execute(statement)
    existing_customer = result.scalar_one_or_none()
    if not existing_customer:
        raise HTTPException(status_code=401, detail="Неверное имя или пароль")
    if not verify_password(customer.password, existing_customer.password_hash):
        raise HTTPException(status_code=401, detail="Неверное имя или пароль")
    
    set_auth_cookie(response, customer_id=existing_customer.id)
    return existing_customer

@router.post("/logout", status_code=204)
def logout_customer(response: Response):
    """Выход из аккаунта."""
    delete_auth_cookie(response)
    return