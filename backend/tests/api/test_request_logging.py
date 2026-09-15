from unittest.mock import patch
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.request_context import get_request_id
from app.main import app
from app.middleware.request_logging import request_logging_middleware


@pytest.mark.asyncio
async def test_response_contains_generated_request_id() -> None:
    # Arrange
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        # Act
        response = await client.get(
            "/health",
        )

        request_id = response.headers["X-Request-ID"]

        # Assert
        assert response.status_code == 200
        assert str(UUID(request_id)) == request_id

    assert get_request_id() is None


@pytest.mark.asyncio
async def test_existing_request_id_is_returned() -> None:
    # Arrange
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        # Act
        response = await client.get(
            "/health",
            headers={
                "X-Request-ID": "client-request-id",
            },
        )

        request_id = response.headers["X-Request-ID"]

        # Assert
        assert response.status_code == 200
        assert request_id == "client-request-id"


@pytest.mark.asyncio
async def test_successful_request_is_logged() -> None:
    # Arrange
    transport = ASGITransport(app=app)

    with patch(
        "app.middleware.request_logging.logger",
    ) as logger_mock:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            await client.get(
                "/health",
                headers={
                    "X-Request-ID": "client-request-id",
                },
            )

            logger_mock.info.assert_called_once()

            call_arguments = logger_mock.info.call_args

            assert call_arguments.args == ("request completed",)

            log_context = call_arguments.kwargs["extra"]

            assert log_context["request_id"] == "client-request-id"
            assert log_context["method"] == "GET"
            assert log_context["path"] == "/health"
            assert log_context["status_code"] == 200
            assert isinstance(log_context["duration_ms"], float)
            assert log_context["duration_ms"] >= 0

        assert get_request_id() is None


@pytest.mark.asyncio
async def test_failed_request_is_logged() -> None:
    # Arrange
    test_app = FastAPI()
    test_app.middleware("http")(request_logging_middleware)

    @test_app.get("/fail")
    async def failing_endpoint() -> dict[str, str]:
        raise RuntimeError("unexpected failure")

    transport = ASGITransport(app=test_app)

    with patch(
        "app.middleware.request_logging.logger",
    ) as logger_mock:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                "/fail",
                headers={
                    "X-Request-ID": "failed-request-id",
                },
            )

        # Assert
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error"}
        assert response.headers["X-Request-ID"] == "failed-request-id"

        logger_mock.exception.assert_called_once()
        call_arguments = logger_mock.exception.call_args

        assert call_arguments.args == ("request failed",)

        log_context = call_arguments.kwargs["extra"]

        assert log_context["request_id"] == "failed-request-id"
        assert log_context["method"] == "GET"
        assert log_context["path"] == "/fail"
        assert log_context["status_code"] == 500
        assert isinstance(log_context["duration_ms"], float)
        assert log_context["duration_ms"] >= 0

    assert get_request_id() is None
