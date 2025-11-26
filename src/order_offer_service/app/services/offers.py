from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from order_offer_service.app.core import exceptions
from order_offer_service.app.logging_config import get_logger
from order_offer_service.app.repositories import OfferRepository
from order_offer_service.app.schemas.offers import OfferCreateRequest

logger = get_logger(__name__)


class OfferService:
    def __init__(self, offer_repo: OfferRepository, scooter_client, user_client):
        self.offer_repo = offer_repo
        self.scooter_client = scooter_client
        self.user_client = user_client

    async def create_offer(self, session: AsyncSession, req: OfferCreateRequest):
        scooter = await self.scooter_client.get_scooter(req.scooter_id)
        zone_id = scooter["zone_id"]
        user = await self.user_client.get_user(req.user_id)

        offer = await self.offer_repo.create(
            session,
            user_id=req.user_id,
            scooter_id=req.scooter_id,
            # price_per_minute=prices...,
            # price_unlock=...,
            # deposit=...,
            # ttl=...,
        )
        await session.commit()
        logger.info("offer.created", offer_id=offer.offer_id, user_id=req.user_id, scooter_id=req.scooter_id)
        return offer

