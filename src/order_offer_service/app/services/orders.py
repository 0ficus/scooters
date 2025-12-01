from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from order_offer_service.app.config import get_settings
from order_offer_service.app.core import exceptions
from order_offer_service.app.core.s3 import s3_storage
from order_offer_service.app.logging_config import get_logger
from order_offer_service.app.repositories import OrderRepository
from order_offer_service.app.services.integrations import PaymentClient
from order_offer_service.app.schemas.orders import OrderStartRequest, OrderStopRequest

settings = get_settings()
logger = get_logger(__name__)


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        offer_service,
        payment_client: PaymentClient,
        scooter_client,
    ) -> None:
        self.order_repo = order_repo
        self.offer_service = offer_service
        self.payment_client = payment_client
        self.scooter_client = scooter_client

    async def start_order(self, session: AsyncSession, req: OrderStartRequest):
        user_id = req.user_id
        offer_id = req.offer_id

        existing = await self.order_repo.get_active_by_user(session, user_id)
        if existing:
            return existing

        offer = await self.offer_service.get_valid_offer(session, offer_id, user_id)

        await self.scooter_client.lock_scooter(offer.scooter_id)

        order = await self.order_repo.create(
            session,
            user_id=user_id,
            scooter_id=offer.scooter_id,
            price_per_minute=offer.price_per_minute,
            price_unlock=offer.price_unlock,
            deposit=offer.deposit,
            ttl=offer.ttl,
        )
        await session.flush()

        await self.payment_client.hold_money(user_id, order.order_id, offer.deposit)

        await session.commit()

        logger.info(
            "order.created",
            order_id=order.order_id,
            user_id=order.user_id,
            scooter_id=order.scooter_id,
            time_start=order.time_start,
            price_per_minute=order.price_per_min,
            price_unlock=order.price_unlock,
            deposit=order.deposit,
            ttl=order.ttl,
        )

        return order

    async def get_order(self, session: AsyncSession, order_id: int, user_id: int):
        order = await self.order_repo.get(session, order_id)
        if order is None or order.user_id != user_id:
            raise exceptions.OrderNotFound()
        return order

    async def describe_order(self, session: AsyncSession, order_id: int, user_id: int):
        order = await self.get_order(session, order_id, user_id)
        
        time_end = order.time_finish if order.time_finish else datetime.now(timezone.utc)
        order_duration = int((time_end - order.time_start).total_seconds())
        
        total_price = 0
        if order_duration >= settings.order_minimal_duration_seconds:
            total_price = (order_duration * order.price_per_minute) // 60 + order.price_unlock
        
        return order, total_price

    async def stop_order(self, session: AsyncSession, req: OrderStopRequest):
        order_id = req.order_id
        user_id = req.user_id
        order = await self.order_repo.get(session, order_id)
        if order is None or order.user_id != user_id:
            raise exceptions.OrderNotFound()

        if order.time_finish is None:
            order = await self.order_repo.finish(session, order_id)

        total_amount = 0
        order_duration = int((order.time_finish - order.time_start).total_seconds())
        if order_duration >= settings.order_minimal_duration_seconds:
            total_amount = (order_duration * order.price_per_minute) // 60 + order.price_unlock

        await self.payment_client.clear_money(user_id, order_id, total_amount)
        await self.scooter_client.unlock_scooter(order.scooter_id)

        order_data = order.to_dict()
        order_data["total_amount"] = total_amount
        archive_key = await s3_storage.store_order(order_data, order.ttl)

        await self.order_repo.delete(session, order_id)
        await session.commit()
        return total_amount, archive_key
