import pytest
from uuid import uuid4
from unittest.mock import AsyncMock
from httpx import AsyncClient

from app.main import app
from app.infrastructure.b2b_client import B2BClient
from app.api.v1.routes.products import get_b2b_client

@pytest.fixture
def mock_b2b_client():
    mock = AsyncMock(spec=B2BClient)
    return mock

@pytest.fixture
async def client(mock_b2b_client):
    app.dependency_overrides[get_b2b_client] = lambda: mock_b2b_client
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_similar_returns_up_to_8_from_same_category(client, mock_b2b_client):
    product_id = uuid4()
    
    mock_items = []
    for i in range(10):
        mock_items.append({
            "id": str(uuid4()) if i != 5 else str(product_id),
            "name": f"Product {i}",
            "slug": f"slug-{i}",
            "category": {"id": str(uuid4()), "name": "cat", "level": 1, "path": []},
            "min_price": 100,
            "has_stock": True,
            "images": []
        })
    
    mock_b2b_client.get_similar_products.return_value = {
        "items": mock_items,
        "total_count": 10,
        "limit": 9,
        "offset": 0
    }
    
    response = await client.get(f"/api/v1/catalog/products/{product_id}/similar?limit=8")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 8
    assert all(item["id"] != str(product_id) for item in data)

@pytest.mark.asyncio
async def test_empty_category_returns_200_empty_list(client, mock_b2b_client):
    product_id = uuid4()
    mock_b2b_client.get_similar_products.return_value = {
        "items": [],
        "total_count": 0,
        "limit": 9,
        "offset": 0
    }
    
    response = await client.get(f"/api/v1/catalog/products/{product_id}/similar")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_unknown_product_returns_404(client, mock_b2b_client):
    product_id = uuid4()
    # If the product does not exist, b2b client should raise an error, or we mock it
    from fastapi import HTTPException
    mock_b2b_client.get_similar_products.side_effect = HTTPException(status_code=404, detail="Product not found")
    
    response = await client.get(f"/api/v1/catalog/products/{product_id}/similar")
    assert response.status_code == 404
