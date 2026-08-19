import asyncio
from uuid import uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.database.session import async_session_factory
from app.main import app
from app.security.tokens import create_access_token
from app.tickets.model import TicketStatus
from app.tickets.repository import TicketRepository
from app.users.model import UserRole
from tests.integration.helpers import (
    create_test_ticket,
    create_test_user,
    delete_test_ticket,
    delete_test_user,
)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_support_agent_assigns_open_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )

    access_token = create_access_token(agent.id)

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/assign",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(ticket.id)
        assert response_data["assignee_id"] == str(agent.id)
        assert response_data["status"] == "in_progress"

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

        assert saved_ticket is not None
        assert saved_ticket.assignee_id == agent.id
        assert saved_ticket.status is TicketStatus.IN_PROGRESS

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_cannot_assign_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )

    access_token = create_access_token(customer.id)

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/assign",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == (
            "Only active support agents can assign tickets"
        )

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

        assert saved_ticket is not None
        assert saved_ticket.assignee_id is None
        assert saved_ticket.status is TicketStatus.OPEN

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_admin_cannot_assign_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    admin = await create_test_user(
        email=f"admin-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.ADMIN,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )

    access_token = create_access_token(admin.id)

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/assign",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == (
            "Only active support agents can assign tickets"
        )

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

        assert saved_ticket is not None
        assert saved_ticket.assignee_id is None
        assert saved_ticket.status is TicketStatus.OPEN

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(admin.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_assign_unknown_ticket() -> None:
    # Arrange
    agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    unknown_ticket_id = uuid4()

    access_token = create_access_token(agent.id)

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{unknown_ticket_id}/assign",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == ("Ticket not found")

    finally:
        await delete_test_user(agent.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_assign_already_assigned_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    current_agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    assigned_agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=assigned_agent.id,
    )

    access_token = create_access_token(current_agent.id)

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/assign",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"] == ("Ticket is already assigned")

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

        assert saved_ticket is not None
        assert saved_ticket.assignee_id == assigned_agent.id
        assert saved_ticket.status is TicketStatus.OPEN

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(current_agent.email)
        await delete_test_user(assigned_agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_assign_resolved_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=None,
        status=TicketStatus.RESOLVED,
    )

    access_token = create_access_token(agent.id)

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/assign",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"] == (
            "Ticket cannot be assigned in its current state"
        )

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

        assert saved_ticket is not None
        assert saved_ticket.assignee_id is None
        assert saved_ticket.status is TicketStatus.RESOLVED

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_assignment_rejects_missing_token() -> None:
    # Arrange
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        # Act
        response = await client.post(
            f"/api/v1/tickets/{uuid4()}/assign",
        )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_blocked_support_agent_cannot_assign_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
        is_blocked=True,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )

    access_token = create_access_token(agent.id)

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/assign",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == ("User account is blocked")

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

        assert saved_ticket is not None
        assert saved_ticket.assignee_id is None
        assert saved_ticket.status is TicketStatus.OPEN

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_only_one_agent_can_assign_ticket_concurrently() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    first_agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    second_agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )

    first_access_token = create_access_token(first_agent.id)
    second_access_token = create_access_token(second_agent.id)

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            responses = await asyncio.gather(
                client.post(
                    f"/api/v1/tickets/{ticket.id}/assign",
                    headers={"Authorization": f"Bearer {first_access_token}"},
                ),
                client.post(
                    f"/api/v1/tickets/{ticket.id}/assign",
                    headers={"Authorization": f"Bearer {second_access_token}"},
                ),
            )

        # Assert
        assert sorted(response.status_code for response in responses) == [
            status.HTTP_200_OK,
            status.HTTP_409_CONFLICT,
        ]

        successful_response = next(
            item for item in responses if item.status_code == status.HTTP_200_OK
        )
        conflict_response = next(
            item for item in responses if item.status_code == status.HTTP_409_CONFLICT
        )

        assert successful_response.status_code == status.HTTP_200_OK
        assert conflict_response.status_code == status.HTTP_409_CONFLICT

        successful_data, conflict_data = (
            successful_response.json(),
            conflict_response.json(),
        )

        assert successful_data["status"] == "in_progress"
        assert successful_data["assignee_id"] in {
            str(first_agent.id),
            str(second_agent.id),
        }

        assert conflict_data["detail"] == "Ticket is already assigned"

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

        assert saved_ticket is not None
        assert saved_ticket.status is TicketStatus.IN_PROGRESS
        assert str(saved_ticket.assignee_id) == successful_data["assignee_id"]

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(first_agent.email)
        await delete_test_user(second_agent.email)
        await delete_test_user(customer.email)
