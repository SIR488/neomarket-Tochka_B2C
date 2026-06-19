from typing import List, Dict, Optional
from uuid import UUID
from app.api.v1.schemas.catalog import CategoryNode, CategoryDetailResponse, CategoryParent, CategorySeo, CategoryMetaTags, FilterItem, ListFilter, RangeFilter, SwitchFilter, FiltersResponse
from app.infrastructure.b2b_client import B2BClient
from app.infrastructure.repositories.category_repository import CategoryRepository
from fastapi import HTTPException

class CategoryService:
    def __init__(self, repository: CategoryRepository, b2b_client: B2BClient):
        self.repository = repository
        self.b2b_client = b2b_client

    def _build_tree_with_level_and_path(self, categories: List[Dict]) -> List[CategoryNode]:
        nodes = {}
        orphans = []
        
        # Сначала создаем узлы
        for cat in categories:
            nodes[cat["id"]] = CategoryNode(
                id=cat["id"],
                name=cat["name"],
                parent_id=cat.get("parent_id"),
                level=0,
                path=[],
                children=[]
            )
            
        tree = []
        
        # Затем строим дерево
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
                status_code=422,
                detail={
                    "code": "ORPHAN_NODE",
                    "message": "category hierarchy is broken",
                    "orphan_ids": [str(o) for o in orphans]
                }
            )
            
        # Теперь вычисляем level и path
        def compute_level_and_path(node: CategoryNode, current_level: int, current_path: List[str]):
            node.level = current_level
            node.path = current_path + [node.name]
            for child in node.children:
                compute_level_and_path(child, current_level + 1, node.path)

        for root in tree:
            compute_level_and_path(root, 0, [])

        return tree

    async def get_category_tree(self) -> List[CategoryNode]:
        """Собирает дерево категорий из плоского списка"""
        categories = await self.b2b_client.get_categories()
        return self._build_tree_with_level_and_path(categories)

    async def get_category_flat_tree(self) -> List[CategoryNode]:
        categories = await self.b2b_client.get_categories()
        return categories

    async def get_category_detail(
        self, 
        category_id: UUID, 
        include_product_count: bool = False,
        lang: str = "ru"
    ) -> Optional[CategoryDetailResponse]:
        """Получает детальную информацию о категории"""
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
            if name not in grouped_chars:
                grouped_chars[name] = []
            grouped_chars[name].append(value)

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
