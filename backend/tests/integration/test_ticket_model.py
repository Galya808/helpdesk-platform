from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.database.session import async_session_factory
from app.tickets.model import Ticket, TicketPriority, TicketStatus
from app.users.model import UserRole
from tests.integration.helpers import create_test_user, delete_test_user


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_is_created_with_defaults() -> None:
    # Arrange
    email = f"user-{uuid4()}@example.com"
    password = "strong-password"

    customer = await create_test_user(
        email=email,
        password=password,
    )

    title = "test-title"
    description = "test-description"

    try:
        async with async_session_factory() as session:
            # Act
            ticket = Ticket(
                title=title,
                description=description,
                customer_id=customer.id,
            )

            session.add(ticket)

            await session.flush()
            await session.refresh(ticket)

            # Assert
            assert isinstance(ticket.id, UUID)
            assert ticket.title == title
            assert ticket.description == description
            assert ticket.customer_id == customer.id
            assert ticket.assignee_id is None
            assert ticket.status is TicketStatus.OPEN
            assert ticket.priority is TicketPriority.MEDIUM
            assert ticket.created_at is not None
            assert ticket.updated_at is not None

            await session.rollback()
    finally:
        await delete_test_user(email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_can_be_assigned_to_support_agent() -> None:
    # Arrange
    customer_email = f"user{uuid4()}@example.com"
    agent_email = f"user{uuid4()}@example.com"

    customer = await create_test_user(
        email=customer_email,
        password="strong-password",
    )

    agent = await create_test_user(
        email=agent_email,
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    title = "test-title"
    description = "test-description"

    try:
        async with async_session_factory() as session:
            # Act
            ticket = Ticket(
                title=title,
                description=description,
                customer_id=customer.id,
                assignee_id=agent.id,
                priority=TicketPriority.HIGH,
            )

            session.add(ticket)

            await session.flush()
            await session.refresh(ticket)

            # Assert
            assert ticket.customer_id == customer.id
            assert ticket.assignee_id == agent.id
            assert ticket.priority is TicketPriority.HIGH

            await session.rollback()
    finally:
        await delete_test_user(customer_email)
        await delete_test_user(agent_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_rejects_unknown_customer() -> None:
    # Arrange
    unknown_customer_id = uuid4()

    title = "test-title"
    description = "test-description"

    # Act
    async with async_session_factory() as session:
        ticket = Ticket(
            title=title,
            description=description,
            customer_id=unknown_customer_id,
        )

        session.add(ticket)

        with pytest.raises(IntegrityError):
            await session.flush()

        await session.rollback()
