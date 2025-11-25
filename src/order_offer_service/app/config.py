from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    app_name: str = "OrderOfferService"
    environment: Literal["local", "dev", "prod"] = "local"
    log_level: str = "INFO"

    postgres_dsn: str = Field(
        "postgresql+asyncpg://orders_user:orders_pass@postgres:5432/orders_db", alias="POSTGRES_DSN"
    )
    redis_dsn: str = Field("redis://redis:6379/0", alias="REDIS_DSN")

    s3_endpoint: AnyHttpUrl = Field("http://minio:9000", alias="S3_ENDPOINT")
    s3_access_key: str = Field("minioadmin", alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field("minioadmin", alias="S3_SECRET_KEY")
    s3_bucket: str = Field("orders-archive", alias="S3_BUCKET")
    s3_region: str = Field("eu-central-1", alias="S3_REGION")

    stub_service_base_url: AnyHttpUrl = Field("http://support-stubs:8081", alias="STUB_SERVICE_BASE_URL")


@lru_cache(1)
def get_settings() -> Settings:
    return Settings()

