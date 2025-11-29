from order_offer_service.app.cache.zones import ZonesCache
from order_offer_service.app.cache.configs import ConfigsCache
from order_offer_service.app.repositories import OfferRepository, OrderRepository
from order_offer_service.app.services import (
    OfferService,
    OrderService,
    ConfigClient,
    ZoneClient,
    UserClient,
    ScooterClient,
    PaymentClient,
)

config_cache = ConfigsCache()
zones_cache = ZonesCache()

offer_repository = OfferRepository()
order_repository = OrderRepository()
config_client = ConfigClient()
zone_client = ZoneClient()
user_client = UserClient()
scooter_client = ScooterClient()
payment_client = PaymentClient()

offer_service = OfferService(offer_repository, config_client, zone_client, scooter_client, user_client)
order_service = OrderService(order_repository, offer_service, payment_client, scooter_client)


def get_offer_service() -> OfferService:
    return offer_service


def get_order_service() -> OrderService:
    return order_service


def get_zones_cache() -> ZonesCache:
    return zones_cache


def get_configs_zones_cache() -> ConfigsCache:
    return config_cache
