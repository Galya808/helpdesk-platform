from uuid import uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.database.session import async_session_factory
from app.main import app
from app.security.password import verify_password
from app.users.model import User


async def delete_test_user(email: str) -> None:
    async with async_session_factory() as session, session.begin():
        await session.execute(delete(User).where(User.email == email))


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_user_registration_succeeds() -> None:
    # Arrange
    email = f"user-{uuid4()}@example.com"
    password = "strong-password"

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.post(
                "/api/v1/users/register",
                json={
                    "email": email,
                    "password": password,
                },
            )

            response_data = response.json()

            # Assert HTTP Response
            assert response.status_code == status.HTTP_201_CREATED
            assert response_data["role"] == "customer"
            assert response_data["email"] == email
            assert response_data["id"] is not None
            assert response_data["created_at"] is not None
            assert response_data["updated_at"] is not None
            assert response_data["is_blocked"] is False
            assert "password" not in response_data
            assert "hashed_password" not in response_data

            # Assert database state
            async with async_session_factory() as session:
                result = await session.execute(select(User).where(User.email == email))
                saved_user = result.scalar_one_or_none()

                assert saved_user is not None
                assert saved_user.email == email
                assert saved_user.hashed_password != password
                assert verify_password(password, saved_user.hashed_password)
    finally:
        await delete_test_user(email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_user_registration_with_existing_email() -> None:
    # Arrange
    email = f"user-{uuid4()}@example.com"
    password = "strong-password"

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            first_response = await client.post(
                "/api/v1/users/register",
                json={"email": email, "password": password},
            )

            second_response = await client.post(
                "/api/v1/users/register",
                json={
                    "email": email,
                    "password": password,
                },
            )

        # Assert HTTP responses
        assert first_response.status_code == status.HTTP_201_CREATED
        assert second_response.status_code == status.HTTP_409_CONFLICT
        assert second_response.json() == {
            "detail": "A user with this email already exists"
        }

        # Assert that only one user is created
        async with async_session_factory() as session:
            result = await session.execute(select(User).where(User.email == email))
            saved_users = result.scalars().all()

            assert len(saved_users) == 1

    finally:
        await delete_test_user(email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_user_registration_with_invalid_email() -> None:
    # Arrange
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Act
        response = await client.post(
            "/api/v1/users/register",
            json={"email": "email", "password": "strong-password"},
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_user_registration_with_wrong_password() -> None:
    # Arrange
    email = f"user-{uuid4()}@example.com"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Act
        response = await client.post(
            "/api/v1/users/register",
            json={"email": email, "password": "password"},
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
