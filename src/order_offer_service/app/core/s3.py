from __future__ import annotations

import json
import urllib.parse
from datetime import datetime, timezone
from typing import Any

import aioboto3

from order_offer_service.app.config import get_settings
from order_offer_service.app.logging_config import get_logger

settings = get_settings()
logger = get_logger(__name__)


class S3Storage:
    def __init__(self) -> None:
        self._session = aioboto3.Session()

        self.ttl_grid = [1]
        while self.ttl_grid[-1] < settings.s3_max_ttl_days:
            self.ttl_grid.append(self.ttl_grid[-1] * 2)

    def _client(self):
        return self._session.client(
            "s3",
            endpoint_url=str(settings.s3_endpoint),
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )

    def _round_zone_ttl(self, ttl_days: int) -> int:
        ttl_idx = max(ttl_days - 1, 0).bit_length()
        return self.ttl_grid[min(ttl_idx, len(self.ttl_grid) - 1)]

    async def ensure_bucket(self) -> None:
        async with self._client() as client:
            buckets = await client.list_buckets()
            if any(b["Name"] == settings.s3_bucket for b in buckets.get("Buckets", [])):
                return
            logger.info("s3.bucket.create", bucket=settings.s3_bucket)
            await client.create_bucket(Bucket=settings.s3_bucket)

            await client.put_bucket_lifecycle_configuration(
                Bucket=settings.s3_bucket,
                LifecycleConfiguration={
                    "Rules": [{
                        "ID": f"{ttl}-ttl",
                        "Filter": {"Tag": {"Key": "TTL", "Value": str(ttl)}},
                        "Status": "Enabled",
                        "Expiration": {"Days": ttl}
                    } for ttl in self.ttl_grid]
                }
            )

    async def store_order(self, payload: dict[str, Any], ttl_days: int) -> str:
        timestamp = datetime.now(timezone.utc)
        key = f"orders/year={timestamp.year}/month={timestamp.month}/day={timestamp.day}/{payload['order_id']}.json"
        async with self._client() as client:
            await client.put_object(
                Bucket=settings.s3_bucket,
                Key=key,
                Body=json.dumps(payload).encode("utf-8"),
                ContentType="application/json",
                Tagging=urllib.parse.urlencode({"TTL": str(self._round_zone_ttl(ttl_days))})
            )
        logger.info("s3.order.archived", key=key)
        return key


s3_storage = S3Storage()

