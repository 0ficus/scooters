from datetime import datetime

from pydantic import BaseModel, Field


class OrderStartRequest(BaseModel):
    user_id: int
    offer_id: int


class OrderStartResponse(BaseModel):
    order_id: int


class OrderInfoResponse(BaseModel):
    order_id: int
    user_id: int
    scooter_id: int
    total_price: int
    started_at: datetime = Field(alias="time_start")
    finished_at: datetime | None = Field(default=None, alias="time_finish")


class OrderStopRequest(BaseModel):
    user_id: int
    order_id: int


class OrderStopResponse(BaseModel):
    total_price: int
    archive_key: str

