from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from order_offer_service.app.config import get_settings
from order_offer_service.app.logging_config import get_logger
from order_offer_service.app.models.base import Base

settings = get_settings()
logger = get_logger(__name__)

engine = create_async_engine(settings.postgres_dsn, pool_pre_ping=True, future=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def init_db_schema() -> None:
    logger.info("db.schema.init", dsn=settings.postgres_dsn)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


