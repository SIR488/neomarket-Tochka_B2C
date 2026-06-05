import urllib.request
import urllib.error
from uuid import UUID
from typing import Any, Dict
import json
from fastapi import HTTPException

from app.core.config import settings

class B2BClient:
    def __init__(self, base_url: str = "http://b2b-service:8000", service_key: str = "b2c_to_b2b_key"):
        self.base_url = settings.B2B_SERVICE_URL
        self.service_key = settings.B2B_SERVICE_KEY

    async def _request(self, method: str, path: str, params: dict | None = None):
        url = f"{self.base_url}{path}"
        headers = {
            "Content-Type": "application/json",
            "X-Service-Key": self.service_key,
        }

        req_data = json.dumps(params).encode("utf-8") if params else None
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
            raise HTTPException(status_code=502, detail="B2B service unavailable")

    async def list_products(self, params: Dict[str, Any]):
        return await self._request("GET", "/api/v1/products", params=params)

    async def get_product(self, product_id: UUID):
        return await self._request("GET", f"/api/v1/products/{product_id}")

    async def get_similar_products(self, product_id: UUID, params: Dict[str, Any]):
        return await self._request("GET", f"/api/v1/products/{product_id}/similar", params=params)

    async def get_product_skus(self, product_id: UUID):
        return await self._request("GET", f"/api/v1/products/{product_id}/skus")