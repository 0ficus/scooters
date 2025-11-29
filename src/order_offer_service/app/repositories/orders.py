from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from order_offer_service.app.models import Order


class OrderRepository:
    async def create(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        scooter_id: int,
        price_per_minute: int,
        price_unlock: int,
        deposit: int,
        ttl_days: int,
    ) -> Order:
        order = Order(
            user_id=user_id,
            scooter_id=scooter_id,
            price_per_minute=price_per_minute,
            price_unlock=price_unlock,
            deposit=deposit,
            ttl=ttl_days,
            time_start=datetime.now(timezone.utc),
        )
        session.add(order)
        await session.flush()
        return order

    async def get(self, session: AsyncSession, order_id: int) -> Order | None:
        stmt = select(Order).where(Order.order_id == order_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def finish(self, session: AsyncSession, order_id: int) -> None:
        stmt = update(Order).where(Order.order_id == order_id).values({"time_finish": datetime.now(timezone.utc)})
        await session.execute(stmt)
        await session.commit()
        return await self.get(session, order_id)

    async def delete(self, session: AsyncSession, order_id: int) -> None:
        await session.execute(delete(Order).where(Order.order_id == order_id))

    async def delete_older_than(self, session: AsyncSession, older_than: datetime) -> int:
        stmt = delete(Order).where(Order.time_start < older_than)
        result = await session.execute(stmt)
        return result.rowcount or 0

