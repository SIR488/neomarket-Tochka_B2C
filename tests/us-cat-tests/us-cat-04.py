import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient
from fastapi import HTTPException

from app.infrastructure.b2b_client import B2BClient
from app.main import app


@pytest.fixture
def mock_b2b_client():
    mock = AsyncMock(spec=B2BClient)
    yield mock


@pytest.fixture
async def client(mock_b2b_client):
    app.dependency_overrides[B2BClient] = lambda: mock_b2b_client

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_similar_returns_up_to_8_from_same_category(client, mock_b2b_client):
    mock_b2b_client.get_similar_products.return_value = {
        "items": [
            {"id": "current-123", "title": "Текущий", "cover_image": "img1.jpg"},
            {"id": "sim-1", "title": "Похожий 1", "min_price": 1500},
            {"id": "sim-2", "title": "Похожий 2", "min_price": 2500},
        ]
    }

    response = await client.get(
        "/api/v1/catalog/products/123e4567-e89b-12d3-a456-426614174000/similar",  # ← правильный путь
        params={"category": "456e7890-e89b-12d3-a456-426614174000"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 8
    assert all(item["id"] != "current-123" for item in data["items"])


@pytest.mark.asyncio
async def test_empty_category_returns_200_empty_list(client, mock_b2b_client):
    mock_b2b_client.list_products.return_value = {"items": [], "total": 0}

    response = await client.get(
        "/api/v1/catalog/products",
        params={"filter[category_id]": "00000000-0000-0000-0000-000000000000"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total_count"] == 0


@pytest.mark.asyncio
async def test_unknown_product_returns_404(client, mock_b2b_client):
    mock_b2b_client.get_product.side_effect = HTTPException(
        status_code=404, detail="Product not found"
    )

    response = await client.get("/api/v1/catalog/products/11111111-1111-1111-1111-111111111111")

    assert response.status_code == 404