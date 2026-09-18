import logging
from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.routing import compile_path

from app.core.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_REQUESTS_TOTAL,
)
from app.core.request_context import (
    reset_request_id,
    resolve_request_id,
    set_request_id,
)

RequestHandler = Callable[
    [Request],
    Awaitable[Response],
]

logger = logging.getLogger("app.http")


def get_route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)

    if isinstance(path, str):
        path_regex, _, _ = compile_path(path)

        if path_regex.match(request.url.path):
            return path

    for route_template in request.app.openapi()["paths"]:
        path_regex, _, _ = compile_path(route_template)

        if path_regex.match(request.url.path):
            return route_template

    return "unmatched"


def record_completed_request(
    *,
    request: Request,
    method: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    labels = {
        "method": method,
        "route": get_route_template(request),
        "status_code": str(status_code),
    }
    HTTP_REQUESTS_TOTAL.labels(**labels).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(**labels).observe(duration_seconds)


async def request_logging_middleware(
    request: Request,
    call_next: RequestHandler,
) -> Response:
    record_metrics = request.url.path != "/metrics"
    method = request.method
    request_id = resolve_request_id(request.headers.get("X-Request-ID"))
    token = set_request_id(request_id)
    started_at = perf_counter()

    if record_metrics:
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method).inc()

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        duration_seconds = perf_counter() - started_at
        duration_ms = duration_seconds * 1000

        if record_metrics:
            record_completed_request(
                request=request,
                method=method,
                status_code=response.status_code,
                duration_seconds=duration_seconds,
            )

        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "method": method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response
    except Exception:
        duration_seconds = perf_counter() - started_at
        duration_ms = duration_seconds * 1000

        if record_metrics:
            record_completed_request(
                request=request,
                method=method,
                status_code=500,
                duration_seconds=duration_seconds,
            )

        logger.exception(
            "request failed",
            extra={
                "request_id": request_id,
                "method": method,
                "path": request.url.path,
                "status_code": 500,
                "duration_ms": duration_ms,
            },
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers={"X-Request-ID": request_id},
        )
    finally:
        if record_metrics:
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method).dec()

        reset_request_id(token)
