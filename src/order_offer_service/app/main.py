from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from order_offer_service.app.api.v1 import api_router
from order_offer_service.app.config import get_settings
from order_offer_service.app.core.db import init_db_schema
from order_offer_service.app.core.exceptions import DomainError
from order_offer_service.app.core.s3 import s3_storage
from order_offer_service.app.logging_config import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    default_response_class=JSONResponse,
)
app.include_router(api_router)


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("app.startup", environment=settings.environment)
    await init_db_schema()
    await s3_storage.ensure_bucket()


@app.exception_handler(DomainError)
async def domain_exception_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

