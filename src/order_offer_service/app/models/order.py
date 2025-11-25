from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from order_offer_service.app.models.base import Base


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    scooter_id: Mapped[int] = mapped_column(Integer, nullable=False)
    time_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    time_finish: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    price_per_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    price_unlock: Mapped[int] = mapped_column(Integer, nullable=False)
    deposit: Mapped[int] = mapped_column(Integer, nullable=False)
    ttl: Mapped[int] = mapped_column(Integer, nullable=False)

