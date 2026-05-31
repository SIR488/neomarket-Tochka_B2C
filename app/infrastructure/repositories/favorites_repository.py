from sqlite3 import IntegrityError
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.models import Favorite, Product, ProductSubscription
from app.api.v1.schemas.favorite import SubscriptionEventType

class FavoriteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_favorite(self, customer_id: UUID, product_id: UUID) -> Optional[UUID]:
        product = await self.session.get(Product, product_id)
        if not product:
            return None

        fav = Favorite(customer_id=customer_id, product_id=product_id)
        self.session.add(fav)
        try:
            await self.session.commit()
            await self.session.refresh(fav)
        except IntegrityError:
            await self.session.rollback()
            return None

        return fav.id

    async def get_favorites(self, customer_id: UUID, limit: int = 10, offset: int = 0) -> List[Favorite]:
        query = select(Favorite).where(Favorite.customer_id == customer_id).limit(limit).offset(offset)
        result = await self.session.execute(query)
        favorites = result.scalars().all()
        return list(favorites)

    async def delete_favorite(self, customer_id: UUID, product_id: UUID) -> Optional[UUID]:
        query = select(Favorite).where(Favorite.customer_id == customer_id, Favorite.product_id == product_id)
        result = await self.session.execute(query)

        favorite = result.scalar_one_or_none()
        if not favorite:
            return None

        await self.session.delete(favorite)
        await self.session.commit()

        return favorite.id

    async def add_subscription(self, customer_id: UUID, product_id: UUID, event_type: SubscriptionEventType) -> bool:
        """Добавить подписку на событие"""
        subscription = ProductSubscription(
            customer_id=customer_id,
            product_id=product_id,
            event_type=event_type
        )
        self.session.add(subscription)
        try:
            await self.session.commit()
            return True
        except IntegrityError:
            await self.session.rollback()
            return False

    async def remove_subscription(self, customer_id: UUID, product_id: UUID, event_type: SubscriptionEventType = None) -> int:
        """Удалить подписки"""
        query = select(ProductSubscription).where(
            ProductSubscription.customer_id == customer_id,
            ProductSubscription.product_id == product_id
        )
        if event_type:
            query = query.where(ProductSubscription.event_type == event_type)
        
        result = await self.session.execute(query)
        subscriptions = result.scalars().all()
        
        for sub in subscriptions:
            await self.session.delete(sub)
        
        await self.session.commit()
        return len(subscriptions)

    async def get_subscriptions_by_product(self, product_id: UUID, event_type: SubscriptionEventType = None) -> List[ProductSubscription]:
        """Получить всех подписчиков на товар"""
        query = select(ProductSubscription).where(
            ProductSubscription.product_id == product_id
        )
        if event_type:
            query = query.where(ProductSubscription.event_type == event_type)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_product(self, product_id: UUID) -> Optional[Product]:
        """Проверить существование товара"""
        return await self.session.get(Product, product_id)