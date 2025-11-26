from fastapi import APIRouter

from order_offer_service.app.api.v1.routes_offers import router as offers_router
from order_offer_service.app.api.v1.routes_orders import router as orders_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(offers_router, prefix="/offers", tags=["offers"])
api_router.include_router(orders_router, prefix="/orders", tags=["orders"])

