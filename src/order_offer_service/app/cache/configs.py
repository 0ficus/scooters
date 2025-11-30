from .base import BaseCache
from order_offer_service.app.services.integrations import ConfigClient


class ConfigsCache(BaseCache):
    KEY = "configs"

    def __init__(self, client: ConfigClient, ttl: int = 60):
        super().__init__(ttl=ttl)
        self.client = client

    async def get_configs(self):
        return await self.get_or_set(self.KEY, self.client.obtain_price_coeff_settings)
