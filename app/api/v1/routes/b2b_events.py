from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel

from app.infrastructure.database import get_db
from app.application.services.b2b_events_service import B2BEventsService

router = APIRouter()

class ProductEventPayload(BaseModel):
    idempotency_key: UUID
    product_id: UUID
    status: str

async def get_b2b_events_service(db: AsyncSession = Depends(get_db)) -> B2BEventsService:
    return B2BEventsService(db)

def verify_service_key(x_service_key: str = Header(...)):
    if x_service_key != "b2c_to_b2b_key":
        raise HTTPException(status_code=401, detail="Invalid service key")
    return x_service_key

@router.post("/product", summary="Прием событий по продуктам от B2B")
async def handle_product_event(
    payload: ProductEventPayload,
    service_key: str = Depends(verify_service_key),
    service: B2BEventsService = Depends(get_b2b_events_service)
):
    """
    Вебхук для приема событий блокировки/разблокировки/модерации товаров из B2B.
    """
    return await service.process_product_event(
        idempotency_key=payload.idempotency_key,
        product_id=payload.product_id,
        status=payload.status
    )
