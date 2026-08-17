from uuid import uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.security.tokens import create_access_token
from app.users.model import UserRole
from tests.integration.helpers import (
    create_test_ticket,
    create_test_user,
    delete_test_ticket,
    delete_test_user,
)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_gets_own_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )

    transport = ASGITransport(app=app)

    access_token = create_access_token(customer.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                f"/api/v1/tickets/{ticket.id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(ticket.id)
        assert response_data["customer_id"] == str(customer.id)
        assert response_data["title"] == ticket.title
        assert response_data["description"] == ticket.description
        assert response_data["status"] == "open"
        assert response_data["priority"] == "medium"
        assert response_data["assignee_id"] is None
        assert response_data["updated_at"] is not None
        assert response_data["created_at"] is not None

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_cannot_get_another_customers_ticket() -> None:
    # Arrange
    ticket_owner = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    customer = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=ticket_owner.id,
    )

    transport = ASGITransport(app=app)

    access_token = create_access_token(customer.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                f"/api/v1/tickets/{ticket.id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": "Ticket not found",
        }

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)
        await delete_test_user(ticket_owner.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_unknown_ticket_returns_not_found() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    unknown_ticket_id = uuid4()

    transport = ASGITransport(app=app)

    access_token = create_access_token(customer.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                f"/api/v1/tickets/{unknown_ticket_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": "Ticket not found",
        }

    finally:
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_support_agent_gets_unassigned_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    agent = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )

    transport = ASGITransport(app=app)

    access_token = create_access_token(agent.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                f"/api/v1/tickets/{ticket.id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(ticket.id)
        assert response_data["customer_id"] == str(customer.id)
        assert response_data["title"] == ticket.title
        assert response_data["description"] == ticket.description
        assert response_data["status"] == "open"
        assert response_data["priority"] == "medium"
        assert response_data["assignee_id"] is None
        assert response_data["updated_at"] is not None
        assert response_data["created_at"] is not None

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_support_agent_gets_assigned_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    agent = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=agent.id,
    )

    transport = ASGITransport(app=app)

    access_token = create_access_token(agent.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                f"/api/v1/tickets/{ticket.id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(ticket.id)
        assert response_data["customer_id"] == str(customer.id)
        assert response_data["title"] == ticket.title
        assert response_data["description"] == ticket.description
        assert response_data["status"] == "open"
        assert response_data["priority"] == "medium"
        assert response_data["assignee_id"] == str(agent.id)
        assert response_data["updated_at"] is not None
        assert response_data["created_at"] is not None

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_support_agent_cannot_get_another_agents_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    assigned_agent = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    current_agent = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=assigned_agent.id,
    )

    transport = ASGITransport(app=app)

    access_token = create_access_token(current_agent.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                f"/api/v1/tickets/{ticket.id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": "Ticket not found",
        }

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(assigned_agent.email)
        await delete_test_user(current_agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_admin_gets_any_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    agent = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    admin = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.ADMIN,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=agent.id,
    )

    transport = ASGITransport(app=app)

    access_token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                f"/api/v1/tickets/{ticket.id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(ticket.id)
        assert response_data["customer_id"] == str(customer.id)
        assert response_data["title"] == ticket.title
        assert response_data["description"] == ticket.description
        assert response_data["status"] == "open"
        assert response_data["priority"] == "medium"
        assert response_data["assignee_id"] == str(agent.id)
        assert response_data["updated_at"] is not None
        assert response_data["created_at"] is not None

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(admin.email)
        await delete_test_user(agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_detail_requires_authentication() -> None:
    # Arrange
    random_ticket_id = uuid4()

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        # Act
        response = await client.get(
            f"/api/v1/tickets/{random_ticket_id}",
        )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_detail_rejects_invalid_uuid() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    access_token = create_access_token(customer.id)

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                "/api/v1/tickets/not-a-uuid",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    finally:
        await delete_test_user(customer.email)
