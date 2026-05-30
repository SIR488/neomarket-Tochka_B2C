from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from sqlmodel import SQLModel

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def create_tables():
    """Создать все таблицы при старте"""
    from sqlmodel import SQLModel
    from app.infrastructure.models import (Product, Category, SKU, Stock, Seller, 
                                           CharacteristicValue, Customer, Favorite, 
                                           Cart, CartItem, Address)
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)