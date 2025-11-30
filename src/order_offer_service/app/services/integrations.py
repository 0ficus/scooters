from __future__ import annotations

from typing import Any

import httpx
from redis.asyncio import Redis
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from order_offer_service.app.config import get_settings
from order_offer_service.app.cache.base import ServiceCache
from order_offer_service.app.core import exceptions
from order_offer_service.app.core.redis import cached_get, cached_set, redis_client
from order_offer_service.app.logging_config import get_logger

settings = get_settings()
logger = get_logger(__name__)


class ExternalServiceUnavailable(exceptions.ExternalServiceError):
    message = "external_service_unavailable"


class BaseStubClient:
    def __init__(self, segment: str, critical: bool = False) -> None:
        self.segment = segment
        self.critical = critical

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        base_url = str(settings.stub_service_base_url).rstrip("/")
        path = path.lstrip("/")
        url = f"{base_url}/{path}"

        async def _call() -> Any:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.request(method, url, **kwargs)
            except httpx.RequestError as exc:
                logger.error("stub.connection.error", segment=self.segment, error=str(exc))
                raise ExternalServiceUnavailable(str(exc)) from exc
            if response.status_code >= 400:
                logger.warning(
                    "stub.response.error",
                    segment=self.segment,
                    status=response.status_code,
                    body=response.text,
                )
                raise ExternalServiceUnavailable(response.text)
            return response.json()

        if not self.critical:
            return await _call()

        retryer = AsyncRetrying(
            reraise=True,
            wait=wait_exponential(multiplier=0.2, min=0.2, max=2),
            stop=stop_after_attempt(3),
            retry=retry_if_exception_type((ExternalServiceUnavailable, httpx.RequestError)),
        )
        async for attempt in retryer:
            with attempt:
                return await _call()


class ConfigClient(BaseStubClient):
    def __init__(self, cache_ttl: int = 60) -> None:
        super().__init__("configs")
        self.cache = ServiceCache(cache_ttl)

    async def obtain_price_coeff_settings(self) -> dict[str, Any]:
        return await self._request("GET", "/configs/price_coeff_settings")

    async def get_price_coeff_settings(self) -> dict[str, Any]:
        return await self.cache.get_or_set("configs", self.obtain_price_coeff_settings)


class ZoneClient(BaseStubClient):
    def __init__(self, cache_ttl: int = 600) -> None:
        super().__init__("zones")
        self.cache = ServiceCache(cache_ttl)

    async def obtain_zone(self, zone_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/zones/{zone_id}")

    async def get_zone(self, zone_id: str) -> dict[str, Any]:
        return await self.cache.get_or_set(f"zones:{zone_id}", self.obtain_zone, zone_id)


class UserClient(BaseStubClient):
    def __init__(self) -> None:
        super().__init__("users")

    async def get_user(self, user_id: int) -> dict[str, Any]:
        try:
            return await self._request("GET", f"/users/{user_id}")
        except ExternalServiceUnavailable:
            logger.warning("users.fallback", user_id=user_id)
            return {"user_id": user_id, "has_subscribtion": False, "trusted": False}


class ScooterClient(BaseStubClient):
    def __init__(self) -> None:
        super().__init__("scooters", critical=True)

    async def _scooter_action(self, scooter_id: int, action: str) -> None:
        payload = await self._request("PUT", f"/scooters/{scooter_id}/{action}")
        if not payload.get("success", False):
            raise exceptions.ScooterUnavailable()

    async def get_scooter(self, scooter_id: int, require_available: bool = True) -> dict[str, Any]:
        payload = await self._request("GET", f"/scooters/{scooter_id}")
        if require_available and not payload.get("available", True):
            raise exceptions.ScooterUnavailable()
        return payload

    async def lock_scooter(self, scooter_id: int) -> None:
        await self._scooter_action(scooter_id, "lock")

    async def unlock_scooter(self, scooter_id: int) -> None:
        await self._scooter_action(scooter_id, "unlock")


class PaymentClient(BaseStubClient):
    def __init__(self) -> None:
        super().__init__("payments", critical=True)

    async def _do_payment(self, user_id: int, order_id: int, amount: float, action: str) -> None:
        payload = await self._request("PUT", f"/payments/{user_id}/{order_id}/{action}", params={"amount": amount})
        if not payload.get("success", False):
            raise exceptions.PaymentDeclined()

    async def hold_money(self, user_id: int, order_id: int, amount: float) -> None:
        await self._do_payment(user_id, order_id, amount, "hold")

    async def clear_money(self, user_id: int, order_id: int, amount: float) -> None:
        await self._do_payment(user_id, order_id, amount, "clear")
