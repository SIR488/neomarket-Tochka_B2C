from app.api.v1.schemas.catalog import FilterItem, ListFilter, RangeFilter
from typing import List, Dict, Optional
from uuid import UUID
from fastapi import HTTPException, status

from app.infrastructure.b2b_client import B2BClient
from app.infrastructure.repositories.category_repository import CategoryRepository
from app.api.v1.schemas.catalog import (
    CategoryNode, CategoryNodeShort, CategoryDetailResponse,
    CategoryParent, CategorySeo, CategoryMetaTags, FiltersResponse
)
from app.api.v1.schemas.error import Error

class CategoryService:
        def __init__(self, repository: CategoryRepository):
            self.b2b_client = B2BClient()
            self.repository = repository

        async def _build_tree_with_level_and_path(self, categories):
            nodes: Dict[UUID, CategoryNode] = {
                cat.id: CategoryNode(
                    id=cat.id,
                    name=cat.name,
                    parent_id=cat.parent_id,
                    level=0,
                    path=[],
                    children=[]
                )
                for cat in categories
            }

            tree: List[CategoryNode] = []
            orphans: List[UUID] = []

            for node in nodes.values():
                if node.parent_id is None:
                    tree.append(node)
                else:
                    parent = nodes.get(node.parent_id)
                    if parent is not None:
                        parent.children.append(node)
                    else:
                        orphans.append(node.id)
                        tree.append(node)

            if orphans:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=Error(
                        code="ORPHAN_NODE",
                        message="Обнаружена сломанная иерархия категорий",
                        details={
                            "orphan_ids": [str(oid) for oid in orphans],
                            "description": "Некоторые категории ссылаются на несуществующий parent_id"
                        }
                    ).model_dump()
                )

            def calculate_level_and_path(node: CategoryNode, current_level: int = 0, current_path: List[str] = None):
                if current_path is None:
                    current_path = []

                node.level = current_level
                node.path = current_path + [node.name]

                for child in node.children:
                    calculate_level_and_path(child, current_level + 1, node.path)

            for root in tree:
                calculate_level_and_path(root)

            return tree

        async def get_category_tree(self) -> List[CategoryNode]:
            categories = await self.b2b_client.get_categories()
            if not categories:
                return []
            return await self._build_tree_with_level_and_path(categories)

        async def get_category_flat_tree(self) -> List[CategoryNodeShort]:
            categories = await self.repository.get_all_active()
            if not categories:
                return []
            tree = await self._build_tree_with_level_and_path(categories)

            flat: List[CategoryNodeShort] = []

            def flatten(node: CategoryNode):
                flat.append(CategoryNodeShort(
                    id=node.id,
                    name=node.name,
                    parent_id=node.parent_id,
                    level=node.level,
                    path=node.path
                ))
                for child in node.children:
                    flatten(child)

            for root in tree:
                flatten(root)

            flat.sort(key=lambda x: x.path)
            return flat

        async def get_category_detail(
                self,
                category_id: UUID,
                include_product_count: bool = False,
                lang: str = "ru"
        ) -> Optional[CategoryDetailResponse]:
            cat = await self.repository.get_by_id(category_id)
            if not cat:
                return None

            parent_data = None
            if cat.parent_id:
                parent = await self.repository.get_by_id(cat.parent_id)
                if parent:
                    parent_data = CategoryParent(
                        id=parent.id,
                        name=parent.name,
                        slug=parent.slug
                    )

            product_count = None
            if include_product_count:
                product_count = await self.repository.get_product_count(category_id)

            return CategoryDetailResponse(
                id=cat.id,
                name=cat.name,
                slug=cat.slug,
                description=cat.description,
                parent=parent_data,
                product_count=product_count,
                seo=CategorySeo(
                    title=cat.seo_title or cat.name,
                    description=cat.seo_description or "",
                    keywords=[]
                ),
                meta_tags=CategoryMetaTags(
                    og_title=cat.seo_title or cat.name,
                    og_description=cat.seo_description or cat.description,
                ),
                image_url=cat.image_url,
                is_active=cat.is_active,
                created_at=cat.created_at,
                updated_at=cat.updated_at
            )

        async def get_category_filters(self, category_id: UUID) -> Optional[FiltersResponse]:
            data = await self.repository.get_category_filters(category_id)
            if data is None:
                return None

            items: List[FilterItem] = []
            grouped_chars: Dict[str, List[str]] = {}

            for name, value in data["characteristics"]:
                grouped_chars.setdefault(name, []).append(value)

            for name, values in grouped_chars.items():
                items.append(ListFilter(
                    slug=name.lower(),
                    name=name,
                    value=values
                ))

            if data["min_price"] is not None and data["max_price"] is not None:
                items.append(RangeFilter(
                    slug="price",
                    name="Цена",
                    min=float(data["min_price"] / 100),
                    max=float(data["max_price"] / 100)
                ))

            return FiltersResponse(items=items)
