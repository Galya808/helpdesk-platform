from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app, follow_redirects=False) as client:
        yield client


def test_get_health_returns_http_200(client):
    # Arrange
    test_client = client

    # Act
    response = test_client.get("/health")
    body = response.json()

    # Assert
    assert response.status_code == 200
    assert body == {"status": "ok"}
