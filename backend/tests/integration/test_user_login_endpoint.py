from uuid import uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.security.tokens import decode_access_token
from tests.integration.helpers import create_test_user, delete_test_user


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_successful_login() -> None:
    # Arrange
    email = f"user-{uuid4()}@example.com"
    password = "strong-password"

    created_user = await create_test_user(email, password)

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": email,
                    "password": password,
                },
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response_data["token_type"] == "bearer"
        assert isinstance(response_data["access_token"], str)

        token_subject = decode_access_token(
            response_data["access_token"],
        )

        assert token_subject == created_user.id

    finally:
        await delete_test_user(email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_login_with_unknown_email() -> None:
    # Arrange
    email = f"user-{uuid4()}@example.com"
    password = "strong-password"

    transport = ASGITransport(app=app)

    # Act
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )

        response_data = response.json()

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response_data == {"detail": "Invalid email or password"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_login_with_wrong_password() -> None:
    # Arrange
    email = f"user-{uuid4()}@example.com"
    password = "strong-password"

    await create_test_user(
        email=email,
        password=password,
    )

    transport = ASGITransport(app=app)

    # Act
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": email,
                    "password": "incorrect-password",
                },
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response_data == {"detail": "Invalid email or password"}
        assert response.headers["WWW-Authenticate"] == "Bearer"
    finally:
        await delete_test_user(email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_login_blocked_user() -> None:
    # Arrange
    email = f"user-{uuid4()}@example.com"
    password = "strong-password"

    transport = ASGITransport(app=app)

    await create_test_user(
        email=email,
        password=password,
        is_blocked=True,
    )

    # Act
    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": email,
                    "password": password,
                },
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response_data == {"detail": "User account is blocked"}
        assert "access_token" not in response_data

    finally:
        await delete_test_user(email=email)
