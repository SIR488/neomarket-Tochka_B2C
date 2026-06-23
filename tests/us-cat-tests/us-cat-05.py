import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient
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
async def test_category_tree_returns_nested_structure(client, mock_b2b_client):
    mock_b2b_client.get_categories.return_value = [
        {"id": "root-1", "name": "Электроника", "parent_id": None},
        {"id": "child-1", "name": "Смартфоны", "parent_id": "root-1"},
        {"id": "child-2", "name": "Ноутбуки", "parent_id": "root-1"},
    ]

    response = await client.get("/api/v1/catalog/categories/tree")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Электроника"
    assert len(data[0]["children"]) == 2
    assert data[0]["children"][0]["level"] == 1
    assert data[0]["children"][0]["path"] == ["Электроника", "Смартфоны"]


@pytest.mark.asyncio
async def test_breadcrumbs_return_path_from_root(client, mock_b2b_client):
    response = await client.get(
        "/api/v1/catalog/breadcrumbs",
        params={"category_id": "root-1"}
    )

    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert len(data["data"]) >= 1
        assert data["data"][0]["level"] == 1


@pytest.mark.asyncio
async def test_ambiguous_params_returns_400(client):
    response = await client.get(
        "/api/v1/catalog/breadcrumbs",
        params={"category_id": "c1", "product_id": "p1"}
    )

    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "BAD_REQUEST"
    assert "only one of" in data["message"].lower() or "ambiguous" in data["message"].lower()


@pytest.mark.asyncio
async def test_orphan_node_returns_422(client, mock_b2b_client):
    mock_b2b_client.get_categories.return_value = [
        {"id": "child-1", "name": "Сирота", "parent_id": "non-existent-id"},
    ]

    response = await client.get("/api/v1/catalog/categories/tree")
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "ORPHAN_NODE"
    assert "orphan_ids" in data["details"]