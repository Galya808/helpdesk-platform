import logging
from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request, Response

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


async def request_logging_middleware(
    request: Request,
    call_next: RequestHandler,
) -> Response:
    request_id = resolve_request_id(request.headers.get("X-Request-ID"))
    token = set_request_id(request_id)
    started_at = perf_counter()

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        duration_ms = (perf_counter() - started_at) * 1000
        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response
    except Exception:
        duration_ms = (perf_counter() - started_at) * 1000
        logger.exception(
            "request failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "duration_ms": duration_ms,
            },
        )
        raise
    finally:
        reset_request_id(token)
