from datetime import datetime, timedelta

from pydantic import BaseModel


class OfferCreateRequest(BaseModel):
    user_id: int
    scooter_id: int


class OfferCreateResponse(BaseModel):
    offer_id: int
    price_per_minute: int
    price_unlock: int
    deposit: int
    ttl: int
    expires_at: datetime

    @classmethod
    def from_offer(cls, offer_id: int, ttl: int, created_at: datetime, **kwargs):
        return cls(
            offer_id=offer_id,
            ttl=ttl,
            expires_at=created_at + timedelta(seconds=ttl),
            **kwargs,
        )

