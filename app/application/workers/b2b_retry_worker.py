import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.infrastructure.database import AsyncSessionLocal
from app.infrastructure.models import Order
from app.infrastructure.b2b_client import B2BClient, B2BUnavailableError

logger = logging.getLogger(__name__)

class B2BRetryWorker:
    def __init__(self, b2b_client: B2BClient):
        self.b2b_client = b2b_client
        self._running = False

    async def start(self, interval_seconds: int = 60):
        """Запуск фонового воркера."""
        self._running = True
        logger.info("B2B Retry Worker started.")
        while self._running:
            try:
                await self._process_pending_cancellations()
                await self._process_pending_fulfills()
            except Exception as e:
                logger.error(f"Error in B2B Retry Worker: {e}")
            await asyncio.sleep(interval_seconds)

    def stop(self):
        """Остановка фонового воркера."""
        self._running = False
        logger.info("B2B Retry Worker stopped.")

    async def _process_pending_cancellations(self):
        async with AsyncSessionLocal() as session:
            query = select(Order).options(selectinload(Order.items)).where(Order.status == "CANCEL_PENDING")
            result = await session.execute(query)
            orders = result.scalars().all()
            
            for order in orders:
                items_payload = [{"sku_id": str(item.sku_id), "quantity": item.quantity} for item in order.items]
                try:
                    resp = await self.b2b_client.unreserve(order.id, items_payload)
                    if resp.get("status") == 200:
                        order.status = "CANCELLED"
                        session.add(order)
                        await session.commit()
                        logger.info(f"Order {order.id} successfully cancelled via retry.")
                except B2BUnavailableError:
                    pass  # Оставляем CANCEL_PENDING для следующего цикла
                except Exception as e:
                    logger.error(f"Failed to retry cancel for order {order.id}: {e}")

    async def _process_pending_fulfills(self):
        async with AsyncSessionLocal() as session:
            query = select(Order).options(selectinload(Order.items)).where(
                Order.status == "DELIVERED",
                Order.fulfill_called == False
            )
            result = await session.execute(query)
            orders = result.scalars().all()
            
            for order in orders:
                items_payload = [{"sku_id": str(item.sku_id), "quantity": item.quantity} for item in order.items]
                try:
                    resp = await self.b2b_client.fulfill(order.id, items_payload)
                    if resp.get("status") == 200:
                        order.fulfill_called = True
                        session.add(order)
                        await session.commit()
                        logger.info(f"Order {order.id} successfully fulfilled via retry.")
                except B2BUnavailableError:
                    pass  # Оставляем fulfill_called=False для следующего цикла
                except Exception as e:
                    logger.error(f"Failed to retry fulfill for order {order.id}: {e}")
