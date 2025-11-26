from order_offer_service.app.repositories import OfferRepository, OrderRepository
from order_offer_service.app.services import (
    OfferService,
    OrderService,
    PricingService,
    ConfigClient,
    ZoneClient,
    UserClient,
    ScooterClient,
    PaymentClient,
)

offer_repository = OfferRepository()
order_repository = OrderRepository()
config_client = ConfigClient()
zone_client = ZoneClient()
user_client = UserClient()
scooter_client = ScooterClient()
payment_client = PaymentClient()

offer_service = OfferService(offer_repository, scooter_client, user_client)
order_service = OrderService(order_repository, offer_service, payment_client, scooter_client)


def get_offer_service() -> OfferService:
    return offer_service


def get_order_service() -> OrderService:
    return order_service


