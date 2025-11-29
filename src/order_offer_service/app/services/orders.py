from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from order_offer_service.app.core import exceptions
from order_offer_service.app.core.s3 import s3_storage
from order_offer_service.app.logging_config import get_logger
from order_offer_service.app.repositories import OrderRepository
from order_offer_service.app.services.integrations import PaymentClient
from order_offer_service.app.schemas.orders import OrderStartRequest, OrderStopRequest

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
        pass

