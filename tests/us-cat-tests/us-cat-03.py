import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient

from app.infrastructure.b2b_client import B2BClient
from app.main import app

@pytest.fixture
def mock_b2b_client():
    mock_b2b_client = AsyncMock(spec=B2BClient)
    yield mock_b2b_client


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
def product_card_returns_full_data_with_skus():
    pass

@pytest.mark.asyncio
def cost_price_absent_in_response():
    pass

@pytest.mark.asyncio
def blocked_product_returns_404():
    pass