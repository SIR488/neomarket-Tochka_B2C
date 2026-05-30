import urllib.request
import urllib.error
import json
import asyncio
from typing import List, Dict, Any
from uuid import UUID

class B2BUnavailableError(Exception):
    pass

class B2BClient:
    def __init__(self, base_url: str = "http://b2b-service:8000", service_key: str = "b2c_to_b2b_key"):
        self.base_url = base_url.rstrip("/")
        self.service_key = service_key

    def _make_request(self, method: str, path: str, data: dict | None = None) -> Any:
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
            raise B2BUnavailableError("Сервис товаров временно недоступен, попробуйте позже")

    async def reserve(self, idempotency_key: UUID, items: List[dict]) -> dict:
        data = {
            "idempotency_key": str(idempotency_key),
            "items": [{"sku_id": str(i["sku_id"]), "quantity": i["quantity"]} for i in items]
        }
        resp, status = await asyncio.to_thread(self._make_request, "POST", "/api/v1/reserve", data)
        return {"status": status, "data": resp}

    async def unreserve(self, order_id: UUID, items: List[dict]) -> dict:
        data = {
            "order_id": str(order_id),
            "items": [{"sku_id": str(i["sku_id"]), "quantity": i["quantity"]} for i in items]
        }
        resp, status = await asyncio.to_thread(self._make_request, "POST", "/api/v1/unreserve", data)
        return {"status": status, "data": resp}

    async def fulfill(self, order_id: UUID, items: List[dict]) -> dict:
        data = {
            "order_id": str(order_id),
            "items": [{"sku_id": str(i["sku_id"]), "quantity": i["quantity"]} for i in items]
        }
        resp, status = await asyncio.to_thread(self._make_request, "POST", "/api/v1/fulfill", data)
        return {"status": status, "data": resp}
