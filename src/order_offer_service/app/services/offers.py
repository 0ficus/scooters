from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from order_offer_service.app.config import get_settings
from order_offer_service.app.core import exceptions
from order_offer_service.app.logging_config import get_logger
from order_offer_service.app.repositories import OfferRepository
from order_offer_service.app.schemas.offers import OfferCreateRequest

settings = get_settings()
logger = get_logger(__name__)


class OfferService:
    def __init__(self, offer_repo: OfferRepository, config_client, zone_client, scooter_client, user_client):
        self.offer_repo = offer_repo
        self.config_client = config_client
        self.zone_client = zone_client
        self.scooter_client = scooter_client
        self.user_client = user_client

    async def create_offer(self, session: AsyncSession, req: OfferCreateRequest):
        scooter = await self.scooter_client.get_scooter(req.scooter_id)
        zone_id = scooter["zone_id"]
        zone = await self.zone_client.get_zone(zone_id)
        user = await self.user_client.get_user(req.user_id)
        price_coeff_settings = await self.config_client.get_price_coeff_settings()
        
        actual_price_per_min = zone.get("price_multiplier", 15)
        
        if price_coeff_settings:
            surge = price_coeff_settings.get("surge", 1.0)
            actual_price_per_min = int(actual_price_per_min * float(surge))
            scooter_charge = scooter.get("charge", 100)
            if scooter_charge < settings.low_charge_threshold:
                low_charge_discount = price_coeff_settings.get("low_charge_discount", 1.0)
                actual_price_per_min = int(actual_price_per_min * float(low_charge_discount))

        actual_price_unlock = 0 if user.get("has_subscribtion", False) else zone.get("price_unlock", 50)

        deposit = 0 if user.get("trusted", False) else zone.get("default_deposit", 1000)

        ttl = zone.get("offer_ttl_seconds", 300)

        offer = await self.offer_repo.create(
            session,
            user_id=req.user_id,
            scooter_id=req.scooter_id,
            price_per_minute=actual_price_per_min,
            price_unlock=actual_price_unlock,
            deposit=deposit,
            ttl=ttl,
        )
        await session.commit()
        
        logger.info(
            "offer.created",
            offer_id=offer.offer_id,
            user_id=req.user_id,
            scooter_id=req.scooter_id,
            zone_id=zone_id,
            price_per_minute=actual_price_per_min,
            price_unlock=actual_price_unlock,
            deposit=deposit,
        )
        return offer

    async def get_valid_offer(self, session: AsyncSession, offer_id: int, user_id: int):
        offer = await self.offer_repo.get(session, offer_id)
        if offer is None or offer.user_id != user_id:
            raise exceptions.OfferNotFound()

        expires_at = offer.time_offer_creation + timedelta(seconds=offer.ttl)
        if datetime.now(timezone.utc) > expires_at:
            raise exceptions.OfferExpired()
        return offer

    async def consume_offer(self, session: AsyncSession, offer_id: int):
        await self.offer_repo.remove(session, offer_id)

