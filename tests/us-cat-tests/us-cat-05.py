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
def category_tree_returns_nested_structure():
    pass

@pytest.mark.asyncio
def breadcrumbs_return_path_from_root():
    pass

@pytest.mark.asyncio
def ambiguous_params_returns_400():
    pass

@pytest.mark.asyncio
def orphan_node_returns_422():
    pass