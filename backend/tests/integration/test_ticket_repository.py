from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.database.session import async_session_factory
from app.tickets.model import Ticket, TicketPriority, TicketStatus
from app.tickets.repository import TicketRepository
from tests.integration.helpers import create_test_user, delete_test_user


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_repository_creates_ticket() -> None:
    # Arrange
    email = f"user-{uuid4()}@example.com"
    customer = await create_test_user(
        email=email,
        password="strong-password",
    )

    title = "test-title"
    description = "test-description"
    priority = TicketPriority.HIGH
    try:
        async with async_session_factory() as session:
            repository = TicketRepository(session)

            created_ticket = await repository.create(
                title=title,
                description=description,
                priority=priority,
                customer_id=customer.id,
            )

            ticket_id = created_ticket.id

            assert isinstance(created_ticket.id, UUID)
            assert created_ticket.title == title
            assert created_ticket.description == description
            assert created_ticket.priority is TicketPriority.HIGH
            assert created_ticket.status is TicketStatus.OPEN
            assert created_ticket.customer_id == customer.id
            assert created_ticket.assignee_id is None
            assert created_ticket.created_at is not None
            assert created_ticket.updated_at is not None

            await session.rollback()

        async with async_session_factory() as session:
            statement = select(Ticket).where(Ticket.id == ticket_id)
            result = await session.execute(statement)

            assert result.scalar_one_or_none() is None
    finally:
        await delete_test_user(email)
