import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy import select

from app.infrastructure.models import Stock


@pytest.mark.asyncio
async def test_add_sku_increments_quantity_if_already_in_cart(
    client: AsyncClient, db_session, test_b2b_mock, test_sku
):
    email = f"test_{uuid4()}@example.com"
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
        "date_of_birth": "1990-01-01"
    })
    
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "password123"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    resp1 = await client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={"sku_id": str(test_sku), "quantity": 1}
    )
    assert resp1.status_code == 200
    
    resp2 = await client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={"sku_id": str(test_sku), "quantity": 1}
    )
    assert resp2.status_code == 200
    assert resp2.json()["items_count"] == 2


@pytest.mark.asyncio
async def test_get_cart_enriched_with_b2b_data(
    client: AsyncClient, db_session, test_b2b_mock, test_sku
):
    email = f"test_{uuid4()}@example.com"
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
        "date_of_birth": "1990-01-01"
    })
    
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    await client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={"sku_id": str(test_sku), "quantity": 2}
    )
    
    resp = await client.get("/api/v1/cart/", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["items_count"] == 2
    assert resp.json()["subtotal"] == 2000


@pytest.mark.asyncio
async def test_unavailable_sku_out_of_stock(
    client: AsyncClient, db_session, test_b2b_mock, test_sku, monkeypatch
):
    from app.infrastructure.b2b_client import B2BClient
    
    email = f"test_{uuid4()}@example.com"
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
        "date_of_birth": "1990-01-01"
    })
    
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    await client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={"sku_id": str(test_sku), "quantity": 1}
    )
    
    async def mock_get_sku_by_id_out_of_stock(self, sku_id):
        return {
            "id": str(sku_id),
            "product_id": str(sku_id),
            "price": 1000,
            "available_quantity": 0,
            "is_active": True,
            "name": "Mock SKU"
        }
    
    monkeypatch.setattr(B2BClient, "get_sku_by_id", mock_get_sku_by_id_out_of_stock)
    
    cart_resp = await client.get("/api/v1/cart/", headers=headers)
    assert cart_resp.status_code == 200
    data = cart_resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0].get("unavailable_reason") == "OUT_OF_STOCK"


@pytest.mark.asyncio
async def test_unavailable_sku_blocked(
    client: AsyncClient, db_session, test_b2b_mock, test_sku, monkeypatch
):
    from app.infrastructure.b2b_client import B2BClient
    
    email = f"test_{uuid4()}@example.com"
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
        "date_of_birth": "1990-01-01"
    })
    
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    await client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={"sku_id": str(test_sku), "quantity": 1}
    )
    
    async def mock_get_sku_by_id_blocked(self, sku_id):
        return {
            "id": str(sku_id),
            "product_id": str(sku_id),
            "price": 1000,
            "available_quantity": 100,
            "is_active": False,
            "name": "Mock SKU"
        }
    
    monkeypatch.setattr(B2BClient, "get_sku_by_id", mock_get_sku_by_id_blocked)
    
    cart_resp = await client.get("/api/v1/cart/", headers=headers)
    assert cart_resp.status_code == 200
    data = cart_resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0].get("unavailable_reason") == "PRODUCT_BLOCKED"


@pytest.mark.asyncio
async def test_guest_cart_merged_on_login(
    client: AsyncClient, db_session, test_b2b_mock, test_sku
):
    session_id = uuid4()
    guest_headers = {"X-Session-Id": str(session_id)}
    
    resp = await client.post(
        "/api/v1/cart/items",
        headers=guest_headers,
        json={"sku_id": str(test_sku), "quantity": 3}
    )
    assert resp.status_code == 200
    
    email = f"test_{uuid4()}@example.com"
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
        "date_of_birth": "1990-01-01"
    })
    
    login_resp = await client.post(
        "/api/v1/auth/login",
        headers=guest_headers,
        json={"email": email, "password": "password123"}
    )
    assert login_resp.status_code == 200
    
    token = login_resp.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    
    cart_resp = await client.get("/api/v1/cart/", headers=auth_headers)
    assert cart_resp.status_code == 200
    assert len(cart_resp.json()["items"]) >= 1