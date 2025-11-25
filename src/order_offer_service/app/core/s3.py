from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import aioboto3

from order_offer_service.app.config import get_settings
from order_offer_service.app.logging_config import get_logger

settings = get_settings()
logger = get_logger(__name__)


class S3Storage:
    def __init__(self) -> None:
        self._session = aioboto3.Session()

    def _client(self):
        return self._session.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )

    async def ensure_bucket(self) -> None:
        async with self._client() as client:
            buckets = await client.list_buckets()
            if any(b["Name"] == settings.s3_bucket for b in buckets.get("Buckets", [])):
                return
            logger.info("s3.bucket.create", bucket=settings.s3_bucket)
            await client.create_bucket(Bucket=settings.s3_bucket)

    async def store_order(self, payload: dict[str, Any], zone_id: str) -> str:
        timestamp = datetime.utcnow()
        key = (
            f"orders/zone={zone_id}/year={timestamp.year}/month={timestamp.month}/"
            f"day={timestamp.day}/{payload['order_id']}.json"
        )
        async with self._client() as client:
            await client.put_object(
                Bucket=settings.s3_bucket,
                Key=key,
                Body=json.dumps(payload).encode("utf-8"),
                ContentType="application/json",
            )
        logger.info("s3.order.archived", key=key)
        return key


s3_storage = S3Storage()

