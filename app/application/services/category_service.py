from typing import List, Dict, Optional
from uuid import UUID
from app.infrastructure.repositories.category_repository import CategoryRepository
from app.api.v1.schemas.catalog import CategoryNode, CategoryDetailResponse, CategoryParent, CategorySeo, CategoryMetaTags, FilterItem, ListFilter, RangeFilter, SwitchFilter, FiltersResponse

class CategoryService:
    def __init__(self, repository: CategoryRepository):
        self.repository = repository

    async def get_category_tree(self) -> List[CategoryNode] | None:
        """Собирает дерево категорий из плоского списка"""
        categories = await self.repository.get_all_active()

        nodes: Dict[UUID, CategoryNode] = {
            cat.id: CategoryNode(
                id=cat.id,
                name=cat.name,
                parent_id=cat.parent_id,
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
                    # ← Orphan node обнаружен
                    orphans.append(node.id)
                    tree.append(node)  # временно кладём в корень

        if orphans:
            return None

        return tree

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
