import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, TypedDict
from fastapi import Response, Request
from uuid import UUID
from app.core.config import settings

JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_ACCESS_TOKEN_EXPIRE_DAYS = settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS
JWT_SECURE = settings.JWT_SECURE

class TokenPayload(TypedDict):
    customer_id: str
    exp: int

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(customer_id:UUID) -> str:
    expire = int((datetime.now() + timedelta(days=JWT_ACCESS_TOKEN_EXPIRE_DAYS)).timestamp())
    to_encode=TokenPayload(customer_id=str(customer_id), exp=expire)
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def get_token_from_cookie(request: Request) -> Optional[str]:
    """
    Достает JWT токен из cookie.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    return token

def decode_token(token: str) -> Optional[UUID]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        customer_id = payload.get("customer_id")
        
        if customer_id is None or not isinstance(customer_id, str):
            return None
        
        return UUID(customer_id)
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except (ValueError, TypeError):
        return None

def set_auth_cookie(response: Response, customer_id: UUID):
    """
    Создаёт токен и устанавливает его в HttpOnly куку.
    """
    token = create_access_token(customer_id=customer_id)
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,    # True => передача только по HTTPS
        samesite="lax",  # кука не подставляется при отправке запроса с чужого сайта
        max_age=JWT_ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

def delete_auth_cookie(response: Response) -> None:
    """Удаляет куку с токеном"""
    response.delete_cookie("access_token")