from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.tickets.exceptions import (
    ClosedTicketReassignmentError,
    InvalidTicketAssigneeError,
    TicketNotFoundError,
    TicketReassignmentForbiddenError,
)
from app.tickets.model import Ticket, TicketPriority, TicketStatus
from app.tickets.repository import TicketRepository
from app.tickets.schemas import TicketAssigneeUpdate
from app.tickets.use_cases import ReassignTicket
from app.users.exceptions import UserNotFoundError
from app.users.model import User, UserRole
from app.users.repository import UserRepository


def make_user(role: UserRole, *, is_blocked: bool = False) -> User:
    return User(
        id=uuid4(),
        email=f"user-{uuid4()}@example.com",
        hashed_password="hashed-password",
        role=role,
        is_blocked=is_blocked,
    )


def make_ticket(*, status: TicketStatus = TicketStatus.OPEN) -> Ticket:
    now = datetime.now(UTC)
    return Ticket(
        id=uuid4(),
        title="Test ticket",
        description="Test ticket description",
        customer_id=uuid4(),
        status=status,
        priority=TicketPriority.MEDIUM,
        assignee_id=None,
        created_at=now,
        updated_at=now,
    )


def make_use_case(
    ticket_repository: AsyncMock,
    user_repository: AsyncMock,
) -> ReassignTicket:
    return ReassignTicket(ticket_repository, user_repository)


@pytest.mark.asyncio
async def test_admin_reassigns_ticket() -> None:
    admin = make_user(UserRole.ADMIN)
    agent = make_user(UserRole.SUPPORT_AGENT)
    ticket = make_ticket()
    ticket_repository = AsyncMock(spec=TicketRepository)
    user_repository = AsyncMock(spec=UserRepository)
    ticket_repository.get_by_id_for_update.return_value = ticket
    ticket_repository.save.return_value = ticket
    user_repository.get_by_id.return_value = agent

    result = await make_use_case(ticket_repository, user_repository).execute(
        ticket_id=ticket.id,
        data=TicketAssigneeUpdate(assignee_id=agent.id),
        current_user=admin,
    )

    assert result.assignee_id == agent.id
    ticket_repository.get_by_id_for_update.assert_awaited_once_with(ticket.id)
    user_repository.get_by_id.assert_awaited_once_with(agent.id)
    ticket_repository.save.assert_awaited_once_with(ticket)


@pytest.mark.asyncio
async def test_non_admin_cannot_reassign_ticket() -> None:
    ticket_repository = AsyncMock(spec=TicketRepository)
    user_repository = AsyncMock(spec=UserRepository)

    with pytest.raises(TicketReassignmentForbiddenError):
        await make_use_case(ticket_repository, user_repository).execute(
            ticket_id=uuid4(),
            data=TicketAssigneeUpdate(assignee_id=uuid4()),
            current_user=make_user(UserRole.SUPPORT_AGENT),
        )

    ticket_repository.get_by_id_for_update.assert_not_awaited()


@pytest.mark.asyncio
async def test_unknown_ticket_cannot_be_reassigned() -> None:
    ticket_repository = AsyncMock(spec=TicketRepository)
    user_repository = AsyncMock(spec=UserRepository)
    ticket_repository.get_by_id_for_update.return_value = None

    with pytest.raises(TicketNotFoundError):
        await make_use_case(ticket_repository, user_repository).execute(
            ticket_id=uuid4(),
            data=TicketAssigneeUpdate(assignee_id=uuid4()),
            current_user=make_user(UserRole.ADMIN),
        )

    user_repository.get_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_unknown_assignee_cannot_receive_ticket() -> None:
    ticket = make_ticket()
    ticket_repository = AsyncMock(spec=TicketRepository)
    user_repository = AsyncMock(spec=UserRepository)
    ticket_repository.get_by_id_for_update.return_value = ticket
    user_repository.get_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await make_use_case(ticket_repository, user_repository).execute(
            ticket_id=ticket.id,
            data=TicketAssigneeUpdate(assignee_id=uuid4()),
            current_user=make_user(UserRole.ADMIN),
        )

    ticket_repository.save.assert_not_awaited()


@pytest.mark.parametrize(
    "assignee",
    [
        make_user(UserRole.CUSTOMER),
        make_user(UserRole.ADMIN),
        make_user(UserRole.SUPPORT_AGENT, is_blocked=True),
    ],
)
@pytest.mark.asyncio
async def test_invalid_assignee_cannot_receive_ticket(assignee: User) -> None:
    ticket = make_ticket()
    ticket_repository = AsyncMock(spec=TicketRepository)
    user_repository = AsyncMock(spec=UserRepository)
    ticket_repository.get_by_id_for_update.return_value = ticket
    user_repository.get_by_id.return_value = assignee

    with pytest.raises(InvalidTicketAssigneeError):
        await make_use_case(ticket_repository, user_repository).execute(
            ticket_id=ticket.id,
            data=TicketAssigneeUpdate(assignee_id=assignee.id),
            current_user=make_user(UserRole.ADMIN),
        )

    ticket_repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_closed_ticket_cannot_be_reassigned() -> None:
    ticket = make_ticket(status=TicketStatus.CLOSED)
    ticket_repository = AsyncMock(spec=TicketRepository)
    user_repository = AsyncMock(spec=UserRepository)
    ticket_repository.get_by_id_for_update.return_value = ticket

    with pytest.raises(ClosedTicketReassignmentError):
        await make_use_case(ticket_repository, user_repository).execute(
            ticket_id=ticket.id,
            data=TicketAssigneeUpdate(assignee_id=uuid4()),
            current_user=make_user(UserRole.ADMIN),
        )

    user_repository.get_by_id.assert_not_awaited()
    ticket_repository.save.assert_not_awaited()
