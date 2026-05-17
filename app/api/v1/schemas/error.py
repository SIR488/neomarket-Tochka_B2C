from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class Error(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = Field(default=None)

class ValidationErrorResponse(Error):
    code: str = "VALIDATION_ERROR"
    details: Optional[Dict[str, List[str]]]

class NotFoundErrorResponse(Error):
    code: str = "NOT_FOUND"
    message: str

class ConflictErrorResponse(Error):
    code: str = "CONFLICT"
    message: str

class UnauthorizedErrorResponse(Error):
    code: str = "UNAUTHORIZED"
    message: str = "Необходимо авторизоваться"

class ForbiddenErrorResponse(Error):
    code: str = "FORBIDDEN"
    message: str = "Недостаточно прав"

class BadRequestErrorResponse(Error):
    code: str = "BAD_REQUEST"

class InternalServerErrorResponse(Error):
    code: str = "INTERNAL_SERVER_ERROR"
    message: str = "Внутренняя ошибка сервера"