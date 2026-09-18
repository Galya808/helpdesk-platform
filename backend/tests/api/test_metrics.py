from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from app.core.metrics import METRICS_REGISTRY
from app.main import app
from app.middleware.request_logging import request_logging_middleware


def metric_value(name: str, labels: dict[str, str]) -> float:
    value = METRICS_REGISTRY.get_sample_value(name, labels)
    return float(value or 0)


def completed_request_count() -> float:
    return sum(
        sample.value
        for metric in METRICS_REGISTRY.collect()
        for sample in metric.samples
        if sample.name == "helpdesk_http_requests_total"
    )


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_format() -> None:
    # Arrange
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        # Act
        response = await client.get(
            "/metrics",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"].startswith("text/plain")

        response_text = response.text

        assert "helpdesk_http_requests_total" in response_text
        assert "helpdesk_http_request_duration_seconds" in response_text
        assert "helpdesk_http_requests_in_progress" in response_text


@pytest.mark.asyncio
async def test_successful_request_updates_metrics() -> None:
    labels = {"method": "GET", "route": "/health", "status_code": "200"}
    count_before = metric_value("helpdesk_http_requests_total", labels)
    observations_before = metric_value(
        "helpdesk_http_request_duration_seconds_count",
        labels,
    )
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert metric_value("helpdesk_http_requests_total", labels) == count_before + 1
    assert (
        metric_value("helpdesk_http_request_duration_seconds_count", labels)
        == observations_before + 1
    )
    assert (
        metric_value(
            "helpdesk_http_requests_in_progress",
            {"method": "GET"},
        )
        == 0
    )


@pytest.mark.asyncio
async def test_dynamic_path_uses_route_template_label() -> None:
    labels = {
        "method": "GET",
        "route": "/api/v1/tickets/{ticket_id}",
        "status_code": "401",
    }
    count_before = metric_value("helpdesk_http_requests_total", labels)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/tickets/{uuid4()}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert metric_value("helpdesk_http_requests_total", labels) == count_before + 1


@pytest.mark.asyncio
async def test_metrics_endpoint_is_not_recorded() -> None:
    count_before = completed_request_count()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == status.HTTP_200_OK
    assert completed_request_count() == count_before


@pytest.mark.asyncio
async def test_in_progress_metric_is_incremented_during_request() -> None:
    test_app = FastAPI()
    test_app.middleware("http")(request_logging_middleware)

    @test_app.get("/observe")
    async def observe() -> dict[str, float]:
        value = metric_value(
            "helpdesk_http_requests_in_progress",
            {"method": "GET"},
        )
        return {"in_progress": value}

    transport = ASGITransport(app=test_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/observe")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"in_progress": 1.0}
    assert (
        metric_value(
            "helpdesk_http_requests_in_progress",
            {"method": "GET"},
        )
        == 0
    )


@pytest.mark.asyncio
async def test_failed_request_updates_metrics_with_server_error_status() -> None:
    test_app = FastAPI()
    test_app.middleware("http")(request_logging_middleware)

    @test_app.get("/fail")
    async def fail() -> None:
        raise RuntimeError("unexpected failure")

    labels = {"method": "GET", "route": "/fail", "status_code": "500"}
    count_before = metric_value("helpdesk_http_requests_total", labels)
    transport = ASGITransport(app=test_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/fail")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert metric_value("helpdesk_http_requests_total", labels) == count_before + 1
