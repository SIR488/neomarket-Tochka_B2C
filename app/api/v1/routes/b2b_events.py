from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from typing import Dict, Any

from app.infrastructure.database import get_db
from app.application.services.b2b_events_service import B2BEventsService
from app.core.config import settings

router = APIRouter()


class B2BEvent(BaseModel):
    idempotency_key: UUID
    event_type: str
    occurred_at: datetime
    payload: Dict[str, Any]


async def get_b2b_events_service(db: AsyncSession = Depends(get_db)) -> B2BEventsService:
    return B2BEventsService(db)


def verify_service_key(x_service_key: str = Header(..., alias="X-Service-Key")):
    if x_service_key != settings.B2B_SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Invalid service key")
    return x_service_key


@router.post("/api/v1/b2b/events", summary="Прием событий от B2B", status_code=202)
async def handle_b2b_event(
    event: B2BEvent,
    service_key: str = Depends(verify_service_key),
    service: B2BEventsService = Depends(get_b2b_events_service)
):
    """Вебхук для приема событий из B2B."""
    return await service.process_b2b_event(
        event_type=event.event_type,
        idempotency_key=event.idempotency_key,
        payload=event.payload
    )