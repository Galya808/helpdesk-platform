from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.security.tokens import create_access_token
from tests.integration.helpers import create_test_user, delete_test_user


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_current_user_succeeds() -> None:
    # Arrange
    email = f"user-{uuid4()}@example.com"
    password = "strong-password"

    created_user = await create_test_user(
        email=email,
        password=password,
    )

    access_token = create_access_token(created_user.id)
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(created_user.id)
        assert response_data["email"] == email
        assert response_data["role"] == "customer"
        assert response_data["is_blocked"] is False
        assert response_data["created_at"] is not None
        assert response_data["updated_at"] is not None
        assert "password" not in response_data
        assert "hashed_password" not in response_data

    finally:
        await delete_test_user(email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_current_user_rejects_missing_token() -> None:
    # Arrange
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        # Act
        response = await client.get("/api/v1/users/me")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "detail": "Not authenticated",
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_current_user_rejects_invalid_token() -> None:
    # Arrange
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        # Act
        response = await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": "Bearer invalid-token",
            },
        )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "detail": "Invalid or expired access token",
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_current_user_rejects_expired_token() -> None:
    # Arrange
    user_id = uuid4()

    access_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(seconds=-1),
    )
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        # Act
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
        )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "detail": "Invalid or expired access token",
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_current_user_rejects_missing_user() -> None:
    # Arrange
    user_id = uuid4()
    access_token = create_access_token(user_id)

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        # Act
        response = await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "detail": "Invalid or expired access token",
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_current_user_rejects_blocked_user() -> None:
    # Arrange
    user_id = uuid4()
    email = f"user-{user_id}@example.com"
    password = "strong-password"

    created_user = await create_test_user(
        email=email,
        password=password,
        is_blocked=True,
    )

    access_token = create_access_token(created_user.id)
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                "/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
            )

        response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response_data == {
            "detail": "User account is blocked",
        }
        assert "access_token" not in response_data
    finally:
        await delete_test_user(email)
