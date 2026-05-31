import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional, TypedDict
from fastapi import Response, Request
from uuid import UUID
from app.core.config import settings

JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_REFRESH_TOKEN_EXPIRE_DAYS = getattr(settings, "JWT_REFRESH_TOKEN_EXPIRE_DAYS", 30)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 15)
JWT_SECURE = settings.JWT_SECURE


class TokenPayload(TypedDict):
    sub: str
    exp: int
    type: str


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(customer_id: UUID, token_type: str, expires_delta: timedelta) -> str:
    """Создать JWT токен (access или refresh)"""
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    payload = TokenPayload(
        sub=str(customer_id),
        exp=int(expire.timestamp()),
        type=token_type
    )
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(customer_id: UUID) -> str:
    """Создать access токен (короткоживущий)"""
    return create_token(
        customer_id,
        "access",
        timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(customer_id: UUID) -> str:
    """Создать refresh токен (долгоживущий)"""
    return create_token(
        customer_id,
        "refresh",
        timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )


def create_auth_tokens(customer_id: UUID) -> dict:
    """Создать пару токенов (access + refresh)"""
    access_token = create_access_token(customer_id)
    refresh_token = create_refresh_token(customer_id)
    return {
        "user_id": customer_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


def decode_token(token: str, expected_type: str = "access") -> Optional[UUID]:
    """
    Декодировать и верифицировать токен.
    Возвращает customer_id, если токен валиден и тип совпадает.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        sub = payload.get("sub")
        if sub is None:
            return None
        return UUID(sub)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError, TypeError):
        return None


def get_token_from_header(request: Request) -> Optional[str]:
    """Достать токен из заголовка Authorization: Bearer <token>"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None