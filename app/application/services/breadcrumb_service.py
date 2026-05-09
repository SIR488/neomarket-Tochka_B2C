# app/application/services/breadcrumb_service.py
from typing import Optional
from uuid import UUID

from app.api.v1.schemas.catalog import BreadcrumbResponse, BreadcrumbItem, BreadcrumbMeta

class BreadcrumbService:
    def __init__(self, category_repo, product_repo):
        self.category_repo = category_repo
        self.product_repo = product_repo

    async def get_breadcrumbs(
        self, 
        category_id: Optional[UUID] = None, 
        product_id: Optional[UUID] = None
    ) -> Optional[BreadcrumbResponse]:
        
        target_category_id = category_id
        product_entity = None

        category_exists =  await self.category_repo.get_by_id(target_category_id)
        if not category_exists:
            return None

        if product_id:
            product_entity = await self.product_repo.get_by_id(product_id)
            if not product_entity:
                return None
            target_category_id = product_entity.category_id

        ancestors = await self.category_repo.get_ancestors(target_category_id)

        items = []
        for idx, row in enumerate(ancestors):
            items.append(BreadcrumbItem(
                id=row.id,
                slug=row.slug,
                name=row.name,
                level=idx + 1,
                url=f"/catalog/{row.slug}",
                is_current=(row.id == target_category_id and not product_id)
            ))

        if product_entity:
            items.append(BreadcrumbItem(
                id=product_entity.id,
                slug=product_entity.slug,
                name=product_entity.title,
                level=len(items) + 1,
                url=f"/product/{product_entity.slug}",
                is_current=True
            ))

        return BreadcrumbResponse(
            data=items,
            meta=BreadcrumbMeta(
                resolved_via="product" if product_id else "category",
                category_id=target_category_id,
                product_id=product_id
            )
        )