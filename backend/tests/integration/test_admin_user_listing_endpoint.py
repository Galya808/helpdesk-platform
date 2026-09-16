from uuid import uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.security.tokens import create_access_token
from app.users.model import UserRole
from tests.integration.helpers import create_test_user, delete_test_user


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_admin_lists_users() -> None:
    # Arrange
    admin_email = f"admin-{uuid4()}@example.com"
    customer_email = f"customer-{uuid4()}@example.com"

    try:
        admin = await create_test_user(
            email=admin_email,
            password="strong-password",
            role=UserRole.ADMIN,
        )

        customer = await create_test_user(
            email=customer_email,
            password="strong-password",
            role=UserRole.CUSTOMER,
        )

        access_token = create_access_token(admin.id)
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                "/api/v1/admin/users?page=1&page_size=100",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

            response_data = response.json()
            returned_ids = {item["id"] for item in response_data["items"]}

            # Assert
            assert response.status_code == status.HTTP_200_OK

            assert str(admin.id) in returned_ids
            assert str(customer.id) in returned_ids

            assert response_data["page"] == 1
            assert response_data["page_size"] == 100
            assert response_data["total"] >= 2
            assert response_data["pages"] >= 1

            for item in response_data["items"]:
                assert "password" not in item
                assert "hashed_password" not in item

    finally:
        await delete_test_user(customer_email)
        await delete_test_user(admin_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_cannot_list_users() -> None:
    # Arrange
    customer_email = f"customer-{uuid4()}@example.com"

    try:
        customer = await create_test_user(
            email=customer_email,
            password="strong-password",
            role=UserRole.CUSTOMER,
        )

        access_token = create_access_token(customer.id)
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                "/api/v1/admin/users",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            "detail": "User management is restricted to administrators"
        }

    finally:
        await delete_test_user(customer_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_unauthenticated_user_cannot_list_users() -> None:
    # Arrange
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        # Act
        response = await client.get("/api/v1/admin/users")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers["WWW-Authenticate"] == "Bearer"
