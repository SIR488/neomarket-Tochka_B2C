from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.infrastructure.database import get_db
from app.infrastructure.models import Favorite
from uuid import UUID
from app.api.v1.dependencies.customer_depends import get_current_customer
from app.api.v1.schemas.favorite import FavoriteRead
from sqlmodel import select

router = APIRouter()

@router.post("/{product_id}", response_model=FavoriteRead, status_code=201)
async def create_favorite(
    product_id: UUID, 
    session: AsyncSession = Depends(get_db),
    customer_id: UUID = Depends(get_current_customer)):

    db_favorite = Favorite(product_id=product_id,customer_id=customer_id)
    session.add(db_favorite)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=200, detail="товар уже в избранном")

    await session.refresh(db_favorite)
    
    return db_favorite

@router.get("", response_model=list[FavoriteRead], status_code=200)
async def get_favorites(
    session: AsyncSession = Depends(get_db),
    customer_id: UUID = Depends(get_current_customer)):

    result = await session.execute(
        select(Favorite).where(Favorite.customer_id == customer_id)
    )

    favorites = result.scalars().all()
    return favorites

@router.delete("/{product_id}", status_code=204)
async def delete_favorite(
    product_id: UUID,
    session: AsyncSession = Depends(get_db),
    customer_id: UUID = Depends(get_current_customer)):

    result = await session.execute(
        select(Favorite).where(
            Favorite.customer_id == customer_id,
            Favorite.product_id == product_id
        )
    )
    favorite = result.scalar_one_or_none()
    if not favorite:
        return
    await session.delete(favorite)
    await session.commit()
    return