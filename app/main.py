from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.router import api_router
from app.core.exception_handlers import register_exception_handlers
from app.infrastructure.database import create_tables

from app.infrastructure.b2b_client import B2BClient
from app.application.workers.b2b_retry_worker import B2BRetryWorker
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    
    # Запускаем фоновый воркер
    b2b_client = B2BClient()
    worker = B2BRetryWorker(b2b_client)
    task = asyncio.create_task(worker.start(interval_seconds=60))
    
    yield
    
    # Останавливаем фоновый воркер
    worker.stop()
    await task

def get_application() -> FastAPI:
    application = FastAPI(
        lifespan=lifespan,
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    register_exception_handlers(application)

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
