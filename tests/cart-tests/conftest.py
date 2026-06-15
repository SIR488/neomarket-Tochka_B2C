import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete
from uuid import uuid4

from app.main import app
from app.infrastructure.database import get_db
from app.infrastructure.models import SQLModel, SKU, Stock, Product, Seller
from app.infrastructure.b2b_client import B2BClient


TEST_DATABASE_URL = "postgresql+asyncpg://user:password@db:5432/test_neomarket"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_b2b_mock(monkeypatch):
    async def mock_get_products_by_ids(self, product_ids):
        return {pid: {
            "id": str(pid),
            "product_id": str(pid),
            "title": "Mock Product",
            "price": 1000,
            "available_quantity": 100,
            "is_active": True,
            "image_url": "https://example.com/image.jpg"
        } for pid in product_ids}
    
    async def mock_get_sku_by_id(self, sku_id):
        return {
            "id": str(sku_id),
            "product_id": str(sku_id),
            "price": 1000,
            "available_quantity": 100,
            "is_active": True,
            "name": "Mock SKU"
        }
    
    monkeypatch.setattr(B2BClient, "get_products_by_ids", mock_get_products_by_ids)
    monkeypatch.setattr(B2BClient, "get_sku_by_id", mock_get_sku_by_id)


@pytest_asyncio.fixture(scope="function")
async def test_sku(db_session):
    from app.infrastructure.models import Product, Seller, Stock, Cart, CartItem
    
    product_id = uuid4()
    seller_id = uuid4()
    sku_id = uuid4()
    
    seller = Seller(
        id=seller_id,
        name="Test Seller",
        legal_name="Test Seller LLC",
        inn="1234567890",
        kpp="123456789",
        password_hash="dummy_hash"
    )
    product = Product(
        id=product_id,
        seller_id=seller_id,
        title="Test Product",
        slug="test-product",
        description="",
        status="CREATED"
    )
    sku = SKU(
        id=sku_id,
        product_id=product_id,
        seller_id=seller_id,
        name="Test SKU",
        price=1000,
        status="ACTIVE"
    )
    stock = Stock(id=uuid4(), sku_id=sku_id, quantity=100)
    
    db_session.add(seller)
    db_session.add(product)
    db_session.add(sku)
    db_session.add(stock)
    await db_session.commit()
    
    yield sku_id
    
    await db_session.execute(delete(CartItem).where(CartItem.sku_id == sku_id))
    await db_session.execute(delete(Cart).where(Cart.customer_id.is_(None)).where(Cart.session_id.is_(None)))
    
    await db_session.delete(stock)
    await db_session.delete(sku)
    await db_session.delete(product)
    await db_session.delete(seller)
    await db_session.commit()