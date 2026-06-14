import pytest
from uuid import uuid4
from httpx import AsyncClient


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
async def test_unavailable_sku_shown_with_reason(
    client: AsyncClient, db_session, monkeypatch
):
    """Тест для недоступного SKU (available_quantity: 0)"""
    from app.infrastructure.b2b_client import B2BClient
    
    # Мокируем B2B client для unavailable SKU
    async def mock_get_product_by_sku_unavailable(self, sku_id):
        return {"id": str(sku_id), "product_id": str(sku_id), "price": 1000, "available_quantity": 0, "is_active": True, "name": "Mock SKU"}
    
    monkeypatch.setattr(B2BClient, "get_product_by_sku", mock_get_product_by_sku_unavailable)
    
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
    
    sku_id = uuid4()
    
    resp = await client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={"sku_id": str(sku_id), "quantity": 1}
    )
    assert resp.status_code == 409


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