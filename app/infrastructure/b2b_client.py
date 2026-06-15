import asyncio
import urllib.request
import urllib.error
import json
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import HTTPException

from app.core.config import settings


class B2BUnavailableError(Exception):
    pass


class B2BClient:
    def __init__(self):
        self.base_url = settings.B2B_API_URL
        self.service_key = settings.B2B_SERVICE_KEY

    def _make_request(self, method: str, path: str, data: dict | None = None) -> tuple[Any, int]:
        url = f"{self.base_url}{path}"
        headers = {
            "Content-Type": "application/json",
            "X-Service-Key": self.service_key,
        }
        
        req_data = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8")), response.status
        except urllib.error.HTTPError as e:
            try:
                return json.loads(e.read().decode("utf-8")), e.code
            except Exception:
                return {"error": "unknown"}, e.code
        except (urllib.error.URLError, TimeoutError):
            raise HTTPException(status_code=502, detail="Сервис товаров временно недоступен, попробуйте позже")

    async def get_products_by_ids(self, product_ids: List[UUID]) -> Dict[UUID, dict]:
        if not product_ids:
            return {}
        
        data = {"product_ids": [str(pid) for pid in product_ids]}
        resp, status = await asyncio.to_thread(
            self._make_request, "POST", "/api/v1/public/products/batch", data
        )
        if status != 200:
            raise B2BUnavailableError("Failed to fetch products from B2B")
        
        return {UUID(item["id"]): item for item in resp.get("products", [])}

    async def get_sku_by_id(self, sku_id: UUID) -> Optional[dict]:
        resp, status = await asyncio.to_thread(
            self._make_request, "GET", f"/api/v1/public/skus/{sku_id}", None
        )
        if status == 404:
            return None
        if status != 200:
            raise B2BUnavailableError("Failed to fetch SKU from B2B")
        return resp

    async def reserve(self, idempotency_key: UUID, order_id: UUID, items: List[dict]) -> dict:
        data = {
            "idempotency_key": str(idempotency_key),
            "order_id": str(order_id),
            "items": [{"sku_id": str(i["sku_id"]), "quantity": i["quantity"]} for i in items]
        }
        resp, status = await asyncio.to_thread(self._make_request, "POST", "/api/v1/inventory/reserve", data)
        return {"status": status, "data": resp}

    async def unreserve(self, order_id: UUID, items: List[dict]) -> dict:
        data = {
            "order_id": str(order_id),
            "items": [{"sku_id": str(i["sku_id"]), "quantity": i["quantity"]} for i in items]
        }
        resp, status = await asyncio.to_thread(self._make_request, "POST", "/api/v1/inventory/unreserve", data)
        return {"status": status, "data": resp}

    async def fulfill(self, order_id: UUID, items: List[dict]) -> dict:
        data = {
            "order_id": str(order_id),
            "items": [{"sku_id": str(i["sku_id"]), "quantity": i["quantity"]} for i in items]
        }
        resp, status = await asyncio.to_thread(self._make_request, "POST", "/api/v1/inventory/fulfill", data)
        return {"status": status, "data": resp}

    async def list_products(self, params: Dict[str, Any]):
        resp, status = await asyncio.to_thread(self._make_request, "GET", "/api/v1/public/products", params)
        return resp

    async def get_product(self, product_id: UUID):
        resp, status = await asyncio.to_thread(self._make_request, "GET", f"/api/v1/public/products/{product_id}")
        return resp

    async def get_similar_products(self, product_id: UUID, params: Dict[str, Any]):
        resp, status = await asyncio.to_thread(self._make_request, "GET", f"/api/v1/public/products/{product_id}/similar", params)
        return resp

    async def get_product_skus(self, product_id: UUID):
        resp, status = await asyncio.to_thread(self._make_request, "GET", f"/api/v1/public/products/{product_id}/skus")
        return resp