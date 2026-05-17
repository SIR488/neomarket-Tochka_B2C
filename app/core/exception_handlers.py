from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import NoResultFound
from starlette.responses import JSONResponse

from app.api.v1.schemas.error import (
    Error,
    ValidationErrorResponse,
    NotFoundErrorResponse,
    ConflictErrorResponse,
    UnauthorizedErrorResponse,
    ForbiddenErrorResponse,
    InternalServerErrorResponse,
)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "__root__")
        if field not in details:
            details[field] = []
        details[field].append(error["msg"])

    error_response = ValidationErrorResponse(
        message="Ошибка валидации данных",
        details=details
    )
    return JSONResponse(
        status_code=422,
        content=error_response.model_dump()
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    status_code = exc.status_code
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

    if status_code == 401:
        error = UnauthorizedErrorResponse(message=detail or "Необходимо авторизоваться")
    elif status_code == 403:
        error = ForbiddenErrorResponse(message=detail or "Доступ запрещён")
    elif status_code == 404:
        error = NotFoundErrorResponse(message=detail or "Ресурс не найден")
    elif status_code == 409:
        error = ConflictErrorResponse(message=detail or "Конфликт данных")
    elif status_code == 400:
        error = Error(code="BAD_REQUEST", message=detail or "Некорректный запрос")
    else:
        error = Error(code="HTTP_ERROR", message=detail)

    return JSONResponse(
        status_code=status_code,
        content=error.model_dump()
    )

async def not_found_handler(request: Request, exc: NoResultFound):
    error = NotFoundErrorResponse(message="Ресурс не найден")
    return JSONResponse(
        status_code=404,
        content=error.model_dump()
    )

async def general_exception_handler(request: Request, exc: Exception):
    error = InternalServerErrorResponse()
    return JSONResponse(
        status_code=500,
        content=error.model_dump()
    )

def register_exception_handlers(app: FastAPI):
    app.exception_handler(RequestValidationError)(validation_exception_handler)
    app.exception_handler(HTTPException)(http_exception_handler)
    app.exception_handler(NoResultFound)(not_found_handler)
    app.exception_handler(Exception)(general_exception_handler)