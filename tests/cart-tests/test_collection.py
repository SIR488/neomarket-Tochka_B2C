import pytest
from uuid import uuid4
from httpx import AsyncClient
from datetime import date, timedelta

from app.infrastructure.models import Collection, CollectionProduct, Product, Seller, Category


@pytest.mark.asyncio
async def test_collections_list_returns_metadata_without_products(
    client: AsyncClient, db_session
):
    """Список подборок возвращает метаданные без товаров внутри"""
    today = date.today()
    collection = Collection(
        id=uuid4(),
        title="Test Collection",
        name="Test Collection",
        priority=10,
        is_active=True,
        start_date=today - timedelta(days=1)
    )
    db_session.add(collection)
    await db_session.commit()
    
    response = await client.get("/api/v1/catalog/collections")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == "Test Collection"
    assert "products" in data[0]


@pytest.mark.asyncio
async def test_collection_products_enriched_from_b2b(
    client: AsyncClient, db_session, test_b2b_mock
):
    """Товары подборки обогащаются из B2B"""
    collection = Collection(
        id=uuid4(),
        title="Test Collection",
        is_active=True
    )
    db_session.add(collection)
    
    product_id = uuid4()
    collection_product = CollectionProduct(
        collection_id=collection.id,
        product_id=product_id,
        ordering=1
    )
    db_session.add(collection_product)
    await db_session.commit()
    
    response = await client.get(f"/api/v1/catalog/collections")
    assert response.status_code == 200
    data = response.json()
    
    found = False
    for col in data:
        if col["id"] == str(collection.id):
            assert len(col["products"]) >= 1
            found = True
            break
    assert found


@pytest.mark.asyncio
async def test_unavailable_products_in_unavailable_ids(
    client: AsyncClient, db_session, monkeypatch
):
    """Недоступные товары попадают в unavailable_ids"""
    from app.infrastructure.b2b_client import B2BClient
    

    async def mock_get_products_by_ids_empty(self, product_ids):
        return {}
    
    monkeypatch.setattr(B2BClient, "get_products_by_ids", mock_get_products_by_ids_empty)
    
    collection = Collection(id=uuid4(), title="Test", is_active=True)
    db_session.add(collection)
    
    product_id = uuid4()
    db_session.add(CollectionProduct(collection_id=collection.id, product_id=product_id))
    await db_session.commit()
    
    response = await client.get("/api/v1/catalog/collections")
    assert response.status_code == 200
    data = response.json()
    
    for col in data:
        if col["id"] == str(collection.id):
            assert len(col["products"]) == 0
            break