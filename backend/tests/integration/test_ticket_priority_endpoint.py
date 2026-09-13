from uuid import UUID, uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.database.session import async_session_factory
from app.main import app
from app.security.tokens import create_access_token
from app.tickets.model import Ticket, TicketPriority, TicketStatus
from app.tickets.repository import TicketRepository
from app.users.model import UserRole
from tests.integration.helpers import (
    create_test_ticket,
    create_test_user,
    delete_test_ticket,
    delete_test_user,
)


async def get_saved_ticket(ticket_id: UUID) -> Ticket | None:
    async with async_session_factory() as session:
        repository = TicketRepository(session)
        return await repository.get_by_id(ticket_id)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_assigned_agent_updates_ticket_priority() -> None:
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
        assignee_id=agent.id,
    )

    access_token = create_access_token(agent.id)
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/priority",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
                json={
                    "priority": "high",
                },
            )

            response_data = response.json()

            # Assert
            assert response.status_code == status.HTTP_200_OK

            assert response_data["id"] == str(ticket.id)
            assert response_data["priority"] == "high"
            assert response_data["customer_id"] == str(customer.id)
            assert response_data["assignee_id"] == str(agent.id)

        saved_ticket = await get_saved_ticket(ticket.id)

        assert saved_ticket is not None
        assert saved_ticket.priority is TicketPriority.HIGH
    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_admin_updates_unassigned_ticket_priority() -> None:
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )
    admin = await create_test_user(
        email=f"admin-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.ADMIN,
    )
    ticket = await create_test_ticket(
        title="test-title",
        customer_id=customer.id,
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/priority",
                headers={"Authorization": f"Bearer {create_access_token(admin.id)}"},
                json={"priority": "urgent"},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["priority"] == "urgent"

        saved_ticket = await get_saved_ticket(ticket.id)
        assert saved_ticket is not None
        assert saved_ticket.priority is TicketPriority.URGENT
    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(admin.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("actor_role", [UserRole.SUPPORT_AGENT, UserRole.CUSTOMER])
async def test_unauthorized_user_cannot_update_ticket_priority(
    actor_role: UserRole,
) -> None:
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )
    assigned_agent = await create_test_user(
        email=f"assigned-agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )
    actor = await create_test_user(
        email=f"actor-{uuid4()}@example.com",
        password="strong-password",
        role=actor_role,
    )
    ticket = await create_test_ticket(
        title="test-title",
        customer_id=customer.id,
        assignee_id=assigned_agent.id,
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/priority",
                headers={"Authorization": f"Bearer {create_access_token(actor.id)}"},
                json={"priority": "high"},
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"detail": "Ticket priority change is forbidden"}

        saved_ticket = await get_saved_ticket(ticket.id)
        assert saved_ticket is not None
        assert saved_ticket.priority is TicketPriority.MEDIUM
    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(actor.email)
        await delete_test_user(assigned_agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_blocked_user_cannot_update_ticket_priority() -> None:
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )
    blocked_agent = await create_test_user(
        email=f"blocked-agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
        is_blocked=True,
    )
    ticket = await create_test_ticket(
        title="test-title",
        customer_id=customer.id,
        assignee_id=blocked_agent.id,
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/priority",
                headers={
                    "Authorization": f"Bearer {create_access_token(blocked_agent.id)}"
                },
                json={"priority": "high"},
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"detail": "User account is blocked"}
    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(blocked_agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_closed_ticket_priority_cannot_be_updated() -> None:
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )
    admin = await create_test_user(
        email=f"admin-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.ADMIN,
    )
    ticket = await create_test_ticket(
        title="test-title",
        customer_id=customer.id,
        status=TicketStatus.CLOSED,
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/priority",
                headers={"Authorization": f"Bearer {create_access_token(admin.id)}"},
                json={"priority": "high"},
            )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {"detail": "Closed ticket priority cannot be changed"}
    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(admin.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_missing_ticket_priority_update_returns_not_found() -> None:
    admin = await create_test_user(
        email=f"admin-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.ADMIN,
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/api/v1/tickets/{uuid4()}/priority",
                headers={"Authorization": f"Bearer {create_access_token(admin.id)}"},
                json={"priority": "high"},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Ticket not found"}
    finally:
        await delete_test_user(admin.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_priority_update_rejects_invalid_priority() -> None:
    admin = await create_test_user(
        email=f"admin-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.ADMIN,
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/api/v1/tickets/{uuid4()}/priority",
                headers={"Authorization": f"Bearer {create_access_token(admin.id)}"},
                json={"priority": "critical"},
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    finally:
        await delete_test_user(admin.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_priority_update_requires_authentication() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.patch(
            f"/api/v1/tickets/{uuid4()}/priority",
            json={"priority": "high"},
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers["WWW-Authenticate"] == "Bearer"
