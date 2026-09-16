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
async def test_admin_reassigns_ticket_to_active_agent() -> None:
    emails = [f"user-{uuid4()}@example.com" for _ in range(4)]
    ticket_id = None

    try:
        admin = await create_test_user(emails[0], "strong-password", UserRole.ADMIN)
        customer = await create_test_user(emails[1], "strong-password")
        first_agent = await create_test_user(
            emails[2], "strong-password", UserRole.SUPPORT_AGENT
        )
        second_agent = await create_test_user(
            emails[3], "strong-password", UserRole.SUPPORT_AGENT
        )
        ticket = await create_test_ticket(
            customer_id=customer.id,
            title="Ticket to reassign",
            assignee_id=first_agent.id,
        )
        ticket_id = ticket.id
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/admin/tickets/{ticket.id}/assignee",
                json={"assignee_id": str(second_agent.id)},
                headers={"Authorization": f"Bearer {create_access_token(admin.id)}"},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["assignee_id"] == str(second_agent.id)

        async with async_session_factory() as session:
            persisted = await TicketRepository(session).get_by_id(ticket.id)

        assert persisted is not None
        assert persisted.assignee_id == second_agent.id
    finally:
        if ticket_id is not None:
            await delete_test_ticket(ticket_id)
        for email in reversed(emails):
            await delete_test_user(email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    ("agent_role", "agent_blocked"),
    [(UserRole.CUSTOMER, False), (UserRole.SUPPORT_AGENT, True)],
)
async def test_invalid_agent_cannot_receive_ticket(
    agent_role: UserRole,
    agent_blocked: bool,
) -> None:
    emails = [f"user-{uuid4()}@example.com" for _ in range(3)]
    ticket_id = None

    try:
        admin = await create_test_user(emails[0], "strong-password", UserRole.ADMIN)
        customer = await create_test_user(emails[1], "strong-password")
        agent = await create_test_user(
            emails[2], "strong-password", agent_role, agent_blocked
        )
        ticket = await create_test_ticket(customer.id, "Ticket to reassign")
        ticket_id = ticket.id
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/admin/tickets/{ticket.id}/assignee",
                json={"assignee_id": str(agent.id)},
                headers={"Authorization": f"Bearer {create_access_token(admin.id)}"},
            )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {"detail": "Assignee must be an active support agent"}
    finally:
        if ticket_id is not None:
            await delete_test_ticket(ticket_id)
        for email in reversed(emails):
            await delete_test_user(email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_closed_ticket_cannot_be_reassigned() -> None:
    emails = [f"user-{uuid4()}@example.com" for _ in range(3)]
    ticket_id = None

    try:
        admin = await create_test_user(emails[0], "strong-password", UserRole.ADMIN)
        customer = await create_test_user(emails[1], "strong-password")
        agent = await create_test_user(
            emails[2], "strong-password", UserRole.SUPPORT_AGENT
        )
        ticket = await create_test_ticket(
            customer.id,
            "Closed ticket",
            status=TicketStatus.CLOSED,
        )
        ticket_id = ticket.id
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/admin/tickets/{ticket.id}/assignee",
                json={"assignee_id": str(agent.id)},
                headers={"Authorization": f"Bearer {create_access_token(admin.id)}"},
            )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {"detail": "Closed tickets cannot be reassigned"}
    finally:
        if ticket_id is not None:
            await delete_test_ticket(ticket_id)
        for email in reversed(emails):
            await delete_test_user(email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_non_admin_cannot_reassign_ticket() -> None:
    emails = [f"user-{uuid4()}@example.com" for _ in range(3)]
    ticket_id = None

    try:
        customer = await create_test_user(emails[0], "strong-password")
        other_customer = await create_test_user(emails[1], "strong-password")
        agent = await create_test_user(
            emails[2], "strong-password", UserRole.SUPPORT_AGENT
        )
        ticket = await create_test_ticket(other_customer.id, "Protected ticket")
        ticket_id = ticket.id
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/admin/tickets/{ticket.id}/assignee",
                json={"assignee_id": str(agent.id)},
                headers={"Authorization": f"Bearer {create_access_token(customer.id)}"},
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN
    finally:
        if ticket_id is not None:
            await delete_test_ticket(ticket_id)
        for email in reversed(emails):
            await delete_test_user(email)
