from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.repositories.collection_repository import CollectionRepository
from app.application.services.collection_service import CollectionService
from app.infrastructure.b2b_client import B2BClient


async def get_collection_service(
    db: AsyncSession = Depends(get_db)
) -> CollectionService:
    repository = CollectionRepository(db)
    b2b_client = B2BClient()
    return CollectionService(repository, b2b_client)