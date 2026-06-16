import asyncio
import urllib.request
import urllib.error
import json
import urllib.parse
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from dataclasses import dataclass

from fastapi import HTTPException

from app.core.config import settings


class B2BUnavailableError(Exception):
    pass


class B2BConflictError(Exception):
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"B2B Conflict {status_code}: {detail}")


@dataclass
class ReserveResponse:
    order_id: UUID
    status: str
    reserved_at: datetime


@dataclass
class InventoryOrderResponse:
    order_id: UUID
    status: str
    processed_at: datetime


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

    def _build_query_string(self, params: Dict[str, Any]) -> str:
        if not params:
            return ""
        
        query_parts = []
        for k, v in params.items():
            if v is None:
                continue
            
            if k == "filters" and isinstance(v, dict):
                for f_key, f_val in v.items():
                    if isinstance(f_val, list):
                        for item in f_val:
                            query_parts.append(f"filters[{f_key}]={urllib.parse.quote(str(item))}")
                    else:
                        query_parts.append(f"filters[{f_key}]={urllib.parse.quote(str(f_val))}")
            elif isinstance(v, list):
                for item in v:
                    query_parts.append(f"{k}={urllib.parse.quote(str(item))}")
            else:
                query_parts.append(f"{k}={urllib.parse.quote(str(v))}")
        
        return "&".join(query_parts)

    async def get_products_by_ids(self, product_ids: List[UUID]) -> Dict[UUID, dict]:
        if not product_ids:
            return {}
        
        data = {"product_ids": [str(pid) for pid in product_ids]}
        resp, status = await asyncio.to_thread(
            self._make_request, "POST", "/api/v1/public/products/batch", data
        )
        if status != 200:
            raise B2BUnavailableError("Failed to fetch products from B2B")
        
        if not isinstance(resp, list):
            raise B2BUnavailableError("Invalid response format from B2B")
        
        return {UUID(item["id"]): item for item in resp}

    async def get_sku_by_id(self, sku_id: UUID) -> Optional[dict]:
        resp, status = await asyncio.to_thread(
            self._make_request, "GET", f"/api/v1/public/skus/{sku_id}", None
        )
        if status == 404:
            return None
        if status != 200:
            raise B2BUnavailableError("Failed to fetch SKU from B2B")
        return resp

    async def list_products(self, params: Dict[str, Any]):
        query_string = self._build_query_string(params)
        path = f"/api/v1/public/products?{query_string}" if query_string else "/api/v1/public/products"
        
        resp, status = await asyncio.to_thread(self._make_request, "GET", path, None)
        if status != 200:
            raise B2BUnavailableError("Failed to fetch products from B2B")
        return resp

    async def get_product(self, product_id: UUID):
        resp, status = await asyncio.to_thread(self._make_request, "GET", f"/api/v1/public/products/{product_id}")
        if status != 200:
            raise B2BUnavailableError("Failed to fetch product from B2B")
        return resp

    async def get_similar_products(self, product_id: UUID, params: Dict[str, Any]):
        query_string = self._build_query_string(params)
        path = f"/api/v1/public/products/{product_id}/similar"
        if query_string:
            path += f"?{query_string}"
        
        resp, status = await asyncio.to_thread(self._make_request, "GET", path, None)
        if status != 200:
            raise B2BUnavailableError("Failed to fetch similar products from B2B")
        return resp

    async def get_product_skus(self, product_id: UUID):
        resp, status = await asyncio.to_thread(self._make_request, "GET", f"/api/v1/public/products/{product_id}/skus")
        return resp

    async def get_facets(self, category_id: UUID, dynamic_filters: dict[str, Any] | None = None):
        params = {"category_id": str(category_id)}
        if dynamic_filters:
            params.update(dynamic_filters)
        resp, status = await asyncio.to_thread(self._make_request, "GET", "/api/v1/public/facets", params)
        return resp

    async def reserve(self, idempotency_key: UUID, order_id: UUID, items: List[dict]) -> ReserveResponse:
        data = {
            "idempotency_key": str(idempotency_key),
            "order_id": str(order_id),
            "items": [{"sku_id": str(i["sku_id"]), "quantity": i["quantity"]} for i in items]
        }
        resp, status = await asyncio.to_thread(self._make_request, "POST", "/api/v1/inventory/reserve", data)
        
        if status == 409:
            raise B2BConflictError(status, resp)
        if status != 200:
            raise B2BUnavailableError("Failed to reserve inventory")
        
        return ReserveResponse(
            order_id=UUID(resp["order_id"]),
            status=resp["status"],
            reserved_at=datetime.fromisoformat(resp["reserved_at"])
        )

    async def unreserve(self, order_id: UUID, items: List[dict]) -> InventoryOrderResponse:
        data = {
            "order_id": str(order_id),
            "items": [{"sku_id": str(i["sku_id"]), "quantity": i["quantity"]} for i in items]
        }
        resp, status = await asyncio.to_thread(self._make_request, "POST", "/api/v1/inventory/unreserve", data)
        if status != 200:
            raise B2BUnavailableError("Failed to unreserve inventory")
        return InventoryOrderResponse(
            order_id=UUID(resp["order_id"]),
            status=resp["status"],
            processed_at=datetime.fromisoformat(resp["processed_at"])
        )

    async def fulfill(self, order_id: UUID, items: List[dict]) -> InventoryOrderResponse:
        data = {
            "order_id": str(order_id),
            "items": [{"sku_id": str(i["sku_id"]), "quantity": i["quantity"]} for i in items]
        }
        resp, status = await asyncio.to_thread(self._make_request, "POST", "/api/v1/inventory/fulfill", data)
        if status != 200:
            raise B2BUnavailableError("Failed to fulfill inventory")
        return InventoryOrderResponse(
            order_id=UUID(resp["order_id"]),
            status=resp["status"],
            processed_at=datetime.fromisoformat(resp["processed_at"])
        )