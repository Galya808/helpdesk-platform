from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.middleware.request_logging import request_logging_middleware

settings = get_settings()

configure_logging(
    level=settings.log_level,
    log_format=settings.log_format,
)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.middleware("http")(request_logging_middleware)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok"}
