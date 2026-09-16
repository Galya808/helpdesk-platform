from uuid import uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.database.session import async_session_factory
from app.main import app
from app.security.tokens import create_access_token
from app.users.model import UserRole
from app.users.repository import UserRepository
from tests.integration.helpers import create_test_user, delete_test_user


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_admin_changes_user_role() -> None:
    admin_email = f"admin-{uuid4()}@example.com"
    target_email = f"customer-{uuid4()}@example.com"

    try:
        admin = await create_test_user(
            email=admin_email,
            password="strong-password",
            role=UserRole.ADMIN,
        )
        target = await create_test_user(
            email=target_email,
            password="strong-password",
        )
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/admin/users/{target.id}/role",
                json={"role": "support_agent"},
                headers={"Authorization": f"Bearer {create_access_token(admin.id)}"},
            )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["id"] == str(target.id)
        assert response_data["role"] == "support_agent"
        assert "password" not in response_data
        assert "hashed_password" not in response_data

        async with async_session_factory() as session:
            persisted_user = await UserRepository(session).get_by_id(target.id)

        assert persisted_user is not None
        assert persisted_user.role is UserRole.SUPPORT_AGENT
    finally:
        await delete_test_user(target_email)
        await delete_test_user(admin_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_admin_blocks_user_and_existing_token_loses_access() -> None:
    admin_email = f"admin-{uuid4()}@example.com"
    target_email = f"customer-{uuid4()}@example.com"

    try:
        admin = await create_test_user(
            email=admin_email,
            password="strong-password",
            role=UserRole.ADMIN,
        )
        target = await create_test_user(
            email=target_email,
            password="strong-password",
        )
        admin_token = create_access_token(admin.id)
        target_token = create_access_token(target.id)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            block_response = await client.patch(
                f"/api/v1/admin/users/{target.id}/blocked",
                json={"is_blocked": True},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            protected_response = await client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {target_token}"},
            )

        assert block_response.status_code == status.HTTP_200_OK
        assert block_response.json()["is_blocked"] is True
        assert protected_response.status_code == status.HTTP_403_FORBIDDEN
        assert protected_response.json() == {"detail": "User account is blocked"}
    finally:
        await delete_test_user(target_email)
        await delete_test_user(admin_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_admin_unblocks_user() -> None:
    admin_email = f"admin-{uuid4()}@example.com"
    target_email = f"customer-{uuid4()}@example.com"

    try:
        admin = await create_test_user(
            email=admin_email,
            password="strong-password",
            role=UserRole.ADMIN,
        )
        target = await create_test_user(
            email=target_email,
            password="strong-password",
            is_blocked=True,
        )
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/admin/users/{target.id}/blocked",
                json={"is_blocked": False},
                headers={"Authorization": f"Bearer {create_access_token(admin.id)}"},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_blocked"] is False

        async with async_session_factory() as session:
            persisted_user = await UserRepository(session).get_by_id(target.id)

        assert persisted_user is not None
        assert persisted_user.is_blocked is False
    finally:
        await delete_test_user(target_email)
        await delete_test_user(admin_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_cannot_change_user_role() -> None:
    customer_email = f"customer-{uuid4()}@example.com"
    target_email = f"target-{uuid4()}@example.com"

    try:
        customer = await create_test_user(
            email=customer_email,
            password="strong-password",
        )
        target = await create_test_user(
            email=target_email,
            password="strong-password",
        )
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/admin/users/{target.id}/role",
                json={"role": "admin"},
                headers={"Authorization": f"Bearer {create_access_token(customer.id)}"},
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            "detail": "User management is restricted to administrators"
        }
    finally:
        await delete_test_user(target_email)
        await delete_test_user(customer_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_admin_cannot_change_own_role() -> None:
    admin_email = f"admin-{uuid4()}@example.com"

    try:
        admin = await create_test_user(
            email=admin_email,
            password="strong-password",
            role=UserRole.ADMIN,
        )
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/admin/users/{admin.id}/role",
                json={"role": "customer"},
                headers={"Authorization": f"Bearer {create_access_token(admin.id)}"},
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            "detail": "Administrators cannot change their own account"
        }
    finally:
        await delete_test_user(admin_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_changing_unknown_user_returns_not_found() -> None:
    admin_email = f"admin-{uuid4()}@example.com"

    try:
        admin = await create_test_user(
            email=admin_email,
            password="strong-password",
            role=UserRole.ADMIN,
        )
        unknown_id = uuid4()
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/admin/users/{unknown_id}/role",
                json={"role": "support_agent"},
                headers={"Authorization": f"Bearer {create_access_token(admin.id)}"},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "User not found"}
    finally:
        await delete_test_user(admin_email)
