from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.core.metrics import METRICS_REGISTRY

router = APIRouter(tags=["monitoring"])


@router.get(
    "/metrics",
    include_in_schema=False,
)
def get_metrics() -> Response:
    content = generate_latest(METRICS_REGISTRY)

    return Response(
        content=content,
        media_type=CONTENT_TYPE_LATEST,
    )
