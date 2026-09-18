from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.metrics import router as metrics_router
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(request_logging_middleware)
app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(metrics_router)


@app.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok"}
