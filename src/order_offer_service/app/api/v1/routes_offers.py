from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from order_offer_service.app.core.db import get_db_session
from order_offer_service.app.dependencies import get_offer_service
from order_offer_service.app.schemas.offers import OfferCreateRequest, OfferCreateResponse

router = APIRouter()


@router.put("/create", response_model=OfferCreateResponse)
async def create_offer(
    payload: OfferCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    service=Depends(get_offer_service),
):
    offer = await service.create_offer(session, payload)
    return OfferCreateResponse.from_offer(
        offer_id=offer.offer_id,
        ttl=offer.ttl,
        created_at=offer.time_offer_creation,
        price_per_minute=offer.price_per_minute,
        price_unlock=offer.price_unlock,
        deposit=offer.deposit,
    )

