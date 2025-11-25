from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from order_offer_service.app.models import Offer


class OfferRepository:
    async def create(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        scooter_id: int,
        price_per_minute: int,
        price_unlock: int,
        deposit: int,
        ttl: int,
    ) -> Offer:
        offer = Offer(
            user_id=user_id,
            scooter_id=scooter_id,
            price_per_minute=price_per_minute,
            price_unlock=price_unlock,
            deposit=deposit,
            ttl=ttl,
            time_offer_creation=datetime.now(timezone.utc),
        )
        session.add(offer)
        await session.flush()
        return offer

    async def get(self, session: AsyncSession, offer_id: int) -> Offer | None:
        stmt = select(Offer).where(Offer.offer_id == offer_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def remove(self, session: AsyncSession, offer_id: int) -> None:
        await session.execute(delete(Offer).where(Offer.offer_id == offer_id))

    async def delete_expired(self, session: AsyncSession) -> int:
        stmt = delete(Offer).where(
            Offer.time_offer_creation + func.make_interval(secs=Offer.ttl) < func.now()
        )
        result = await session.execute(stmt)
        return result.rowcount or 0

