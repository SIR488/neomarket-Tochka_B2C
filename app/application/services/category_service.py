from typing import List, Dict, Optional
from uuid import UUID
from app.infrastructure.repositories.category_repository import CategoryRepository
from app.api.v1.schemas.catalog import CategoryNode, CategoryDetailResponse, CategoryParent, CategorySeo, CategoryMetaTags

class CategoryService:
    def __init__(self, repository: CategoryRepository):
        self.repository = repository

    async def get_category_tree(self) -> List[CategoryNode]:
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
        
        for _, node in nodes.items():
            if node.parent_id is None:
                tree.append(node)
            else:
                parent = nodes.get(node.parent_id)
                if parent:
                    parent.children.append(node)
                    
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
            
        product_count = None
        if include_product_count:
            product_count = await self.repository.get_product_count(category_id)

        parent_data = None
        if cat.parent_id:
            parent_data = CategoryParent(
                id=cat.parent_id,
                name="Parent Category",
                slug="parent-slug"
            )

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
                og_title=cat.name,
                og_description=cat.description,
            ),
            image_url=cat.image_url,
            is_active=cat.is_active,
            created_at=cat.created_at,
            updated_at=cat.updated_at
        )
