import httpx
from uuid import UUID
from typing import Any, Dict, Optional
from fastapi import HTTPException


class B2BCategoryClient:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.service_key = "fffsdfsfsd"
        self.timeout = httpx.Timeout(15.0)

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict] = None,
    ):
        url = f"{self.base_url}{path}"
        headers = {
            "X-Service-Key": self.service_key,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                )

                if response.status_code >= 500:
                    raise HTTPException(
                        status_code=502,
                        detail="B2B service unavailable"
                    )

                response.raise_for_status()

                return response.json()

            except httpx.HTTPStatusError as exc:
                try:
                    error_detail = exc.response.json()
                except Exception:
                    error_detail = {"error": exc.response.text}

                raise HTTPException(
                    status_code=exc.response.status_code,
                    detail=error_detail
                )

            except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError):
                raise HTTPException(
                    status_code=502,
                    detail="B2B service unavailable"
                )

    async def list_products(self, params: Dict[str, Any]):
        return await self._request("GET", "/api/v1/public/products", params=params)

    async def get_product(self, product_id: UUID):
        return await self._request("GET", f"/api/v1/public/products/{product_id}")

    async def get_similar_products(self, product_id: UUID, params: Dict[str, Any]):
        return await self._request("GET", f"/api/v1/public/products/{product_id}/similar", params=params)

    async def get_product_skus(self, product_id: UUID):
        return await self._request("GET", f"/api/v1/public/products/{product_id}/skus")

    async def get_facets(self, category_id: UUID, dynamic_filters: dict[str, Any] | None = None):
        params = {"category_id": str(category_id)}
        if dynamic_filters:
            params.update(dynamic_filters)
        return await self._request("GET", "/api/v1/public/facets", params=params)

    async def get_categories(self, parent_id: UUID = None, only_root: bool = False):
        params = {"parent_id": str(parent_id),
                  "only_root": only_root}
        return await self._request("GET", "/api/v1/categories", params=params)