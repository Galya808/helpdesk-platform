from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.tickets.exceptions import TicketCreationForbiddenError
from app.tickets.model import Ticket, TicketPriority
from app.tickets.repository import TicketRepository
from app.tickets.schemas import TicketCreate
from app.tickets.use_cases import CreateTicket
from app.users.model import User, UserRole


@pytest.mark.asyncio
async def test_customer_creates_ticket() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    ticket_data = TicketCreate(
        title="test-title",
        description="test-description",
        priority=TicketPriority.HIGH,
    )

    expected_ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        priority=TicketPriority.HIGH,
        customer_id=customer.id,
    )

    repository = AsyncMock(spec=TicketRepository)
    repository.create.return_value = expected_ticket

    use_case = CreateTicket(repository)

    # Act
    created_ticket = await use_case.execute(
        data=ticket_data,
        current_user=customer,
    )

    # Assert
    assert created_ticket is expected_ticket
    repository.create.assert_awaited_once_with(
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority,
        customer_id=customer.id,
    )


@pytest.mark.asyncio
async def test_support_agent_cannot_create_ticket() -> None:
    # Arrange
    support_agent = User(
        id=uuid4(),
        email="user@example.com",
        hashed_password="hashed-password",
        role=UserRole.SUPPORT_AGENT,
    )

    ticket_data = TicketCreate(
        title="test-title",
        description="test-description",
        priority=TicketPriority.HIGH,
    )

    repository = AsyncMock(spec=TicketRepository)
    use_case = CreateTicket(repository)

    with pytest.raises(TicketCreationForbiddenError):
        await use_case.execute(ticket_data, support_agent)

    repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_admin_cannot_create_ticket() -> None:
    # Arrange
    admin = User(
        id=uuid4(),
        email="user@example.com",
        hashed_password="hashed-password",
        role=UserRole.ADMIN,
    )

    ticket_data = TicketCreate(
        title="test-title",
        description="test-description",
        priority=TicketPriority.HIGH,
    )

    repository = AsyncMock(spec=TicketRepository)
    use_case = CreateTicket(repository)

    with pytest.raises(TicketCreationForbiddenError):
        await use_case.execute(ticket_data, admin)

    repository.create.assert_not_awaited()
