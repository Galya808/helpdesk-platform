from contextvars import ContextVar, Token
from uuid import uuid4

_request_id_context: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)


def resolve_request_id(request_id: str | None) -> str:
    if request_id is not None and request_id.strip():
        return request_id

    return str(uuid4())


def set_request_id(
    request_id: str,
) -> Token[str | None]:
    return _request_id_context.set(request_id)


def get_request_id() -> str | None:
    return _request_id_context.get()


def reset_request_id(
    token: Token[str | None],
) -> None:
    _request_id_context.reset(token)
