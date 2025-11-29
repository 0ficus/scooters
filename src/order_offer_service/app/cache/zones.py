from .base import BaseCache
from app.services.integrations import ZonesClient


class ZonesCache(BaseCache):
    KEY = "zones"

    def __init__(self, client: ZonesClient, ttl: int = 600):
        super().__init__(ttl=ttl)
        self.client = client

    async def get_zones(self):
        return await self.get_or_set(self.KEY, self.client.get_zones)
