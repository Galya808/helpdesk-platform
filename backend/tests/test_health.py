import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_get_health_returns_http_200() -> None:
    # Arrange
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        follow_redirects=False,
    ) as client:
        # Act
        response = await client.get("/health")

    body = response.json()

    # Assert
    assert response.status_code == 200
    assert body == {"status": "ok"}
