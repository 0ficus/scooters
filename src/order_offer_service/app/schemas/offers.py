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

