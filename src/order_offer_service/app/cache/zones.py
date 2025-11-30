from .base import BaseCache
from order_offer_service.app.services.integrations import ZoneClient


class ZonesCache(BaseCache):
    def __init__(self, client: ZoneClient, ttl: int = 600):
        super().__init__(ttl=ttl)
        self.client = client

    async def get_zones(self, key):
        return await self.get_or_set(key, self.client.obtain_zone)
