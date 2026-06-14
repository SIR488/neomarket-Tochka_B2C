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
async def test_catalog_returns_filtered_sorted_products(client, mock_b2b_client):
   pass


@pytest.mark.asyncio
async def test_facets_return_counts_per_filter_value(client, mock_b2b_client):
   pass


@pytest.mark.asyncio
async def test_invalid_sort_returns_400(client):
    pass


@pytest.mark.asyncio
async def test_b2b_unavailable_returns_502(client, mock_b2b_client):
   pass