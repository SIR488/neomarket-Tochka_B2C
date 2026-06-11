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
async def similar_returns_up_to_8_from_same_category(client, mock_b2b_client):
   pass


@pytest.mark.asyncio
async def empty_category_returns_200_empty_list(client, mock_b2b_client):
   pass


@pytest.mark.asyncio
async def unknown_product_returns_404(client):
    pass
