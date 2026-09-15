from uuid import UUID

import pytest

from app.core.request_context import (
    get_request_id,
    reset_request_id,
    resolve_request_id,
    set_request_id,
)


@pytest.mark.parametrize(
    "request_id",
    [
        "client-request-id",
        "550e8400-e29b-41d4-a716-446655440000",
    ],
)
def test_existing_request_id_is_preserved(
    request_id: str,
) -> None:
    # Arrange + Act
    resolved_request_id = resolve_request_id(request_id)

    # Assert
    assert resolved_request_id == request_id


@pytest.mark.parametrize(
    "request_id",
    [
        None,
        "",
        "   ",
    ],
)
def test_missing_request_id_is_generated(
    request_id: str | None,
) -> None:
    # Arrange + Act
    resolved_request_id = resolve_request_id(request_id)

    # Assert
    assert str(UUID(resolved_request_id)) == resolved_request_id


def test_request_id_context_can_be_set_and_reset() -> None:
    # Arrange
    assert get_request_id() is None

    # Act
    token = set_request_id("request-id")

    try:
        # Assert
        assert get_request_id() == "request-id"
    finally:
        reset_request_id(token)

    assert get_request_id() is None
