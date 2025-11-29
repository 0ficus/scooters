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
        pass

    async def get_order(self, session: AsyncSession, order_id: int, user_id: int):
        pass

    async def describe_order(self, session: AsyncSession, order_id: int, user_id: int):
        pass

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

        scooter_id = order.scooter_id
        scooter = await self.scooter_client.get_scooter(scooter_id, require_available=False)
        if not scooter.get("available", True):
            await self.scooter_client.unlock_scooter(scooter_id)

        order_data = order.to_dict()
        order_data["total_amount"] = total_amount
        archive_key = await s3_storage.store_order(order.to_dict(), scooter["zone_id"])

        await self.order_repo.delete(session, order_id)
        await session.commit()
        return total_amount, archive_key
