from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.admin import setup_admin
from app.infrastructure.database import engine
from app.core.config import settings
from app.api.v1.router import api_router
from app.infrastructure.database import create_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield

def get_application() -> FastAPI:
    application = FastAPI(
        lifespan=lifespan,
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix=settings.API_V1_STR)

    @application.get("/health")
    async def health_check():
        return {"status": "ok"}

    return application

app = get_application()

setup_admin(app, engine)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    err = exc.errors()[0]
    msg = f"{err['loc'][-1]}: {err['msg']}"
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": msg},
    )
