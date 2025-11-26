from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from order_offer_service.app.core.db import get_db_session
from order_offer_service.app.dependencies import get_order_service
from order_offer_service.app.schemas.orders import (
    OrderInfoResponse,
    OrderStartRequest,
    OrderStartResponse,
    OrderStopRequest,
    OrderStopResponse,
)

router = APIRouter()


@router.put("/start", response_model=OrderStartResponse)
async def start_order(
    payload: OrderStartRequest,
    session: AsyncSession = Depends(get_db_session),
    service=Depends(get_order_service),
):
    order = await service.start_order(session, payload)
    return OrderStartResponse(order_id=order.order_id)


@router.get("/get", response_model=OrderInfoResponse)
async def get_order(
    user_id: int = Query(...),
    order_id: int = Query(...),
    session: AsyncSession = Depends(get_db_session),
    service=Depends(get_order_service),
):
    order, total_price = await service.describe_order(session, order_id, user_id)
    return OrderInfoResponse(
        order_id=order.order_id,
        user_id=order.user_id,
        scooter_id=order.scooter_id,
        total_price=total_price,
        time_start=order.time_start,
        time_finish=order.time_finish,
    )


@router.put("/stop", response_model=OrderStopResponse)
async def stop_order(
    payload: OrderStopRequest,
    session: AsyncSession = Depends(get_db_session),
    service=Depends(get_order_service),
):
    total_price, archive_key = await service.stop_order(session, payload)
    return OrderStopResponse(total_price=total_price, archive_key=archive_key)


