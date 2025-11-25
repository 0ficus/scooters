from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis

from order_offer_service.app.config import get_settings
from order_offer_service.app.logging_config import get_logger

settings = get_settings()
logger = get_logger(__name__)

redis_client = Redis.from_url(settings.redis_dsn, decode_responses=True)


async def get_redis() -> Redis:
    return redis_client


async def cached_get(client: Redis, key: str) -> Any | None:
    raw = await client.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("redis.json.decode_failed", key=key)
        return None


async def cached_set(client: Redis, key: str, value: Any, ttl: int) -> None:
    serialized = json.dumps(value)
    await client.set(key, serialized, ex=ttl)


