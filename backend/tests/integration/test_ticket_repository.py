from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.database.session import async_session_factory
from app.tickets.model import Ticket, TicketPriority, TicketStatus
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


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_returns_all_tickets() -> None:
    # Arrange
    user_email = f"user-{uuid4()}@example.com"
    user_password = "strong-password"
    user = await create_test_user(
        email=user_email,
        password=user_password,
    )

    ticket1 = await create_test_ticket(
        title="test-title-1",
        description="test-description-1",
        customer_id=user.id,
    )

    ticket2 = await create_test_ticket(
        title="test-title-2",
        description="test-description-2",
        customer_id=user.id,
    )

    try:
        async with async_session_factory() as session:
            # Act
            repository = TicketRepository(session)

            tickets = await repository.list(
                customer_id=None,
                assignee_id=None,
                include_unassigned=False,
                status=None,
                priority=None,
                offset=0,
                limit=100,
            )

        # Assert
        ticket_ids = {ticket.id for ticket in tickets}
        assert ticket1.id in ticket_ids
        assert ticket2.id in ticket_ids

    finally:
        await delete_test_ticket(ticket1.id)
        await delete_test_ticket(ticket2.id)
        await delete_test_user(user_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_filters_tickets_by_customer() -> None:
    # Arrange
    user_email_1 = f"user-{uuid4()}@example.com"
    user_password_1 = "strong-password-1"

    user_email_2 = f"user-{uuid4()}@example.com"
    user_password_2 = "strong-password-2"

    user1 = await create_test_user(
        email=user_email_1,
        password=user_password_1,
    )

    user2 = await create_test_user(
        email=user_email_2,
        password=user_password_2,
    )

    ticket_for_user_1 = await create_test_ticket(
        title="test-title-1",
        description="test-description-1",
        customer_id=user1.id,
    )

    ticket_for_user_2 = await create_test_ticket(
        title="test-title-2",
        description="test-description-2",
        customer_id=user2.id,
    )

    try:
        async with async_session_factory() as session:
            # Act
            repository = TicketRepository(session)

            tickets = await repository.list(
                customer_id=user1.id,
                assignee_id=None,
                include_unassigned=False,
                status=None,
                priority=None,
                offset=0,
                limit=100,
            )

        # Assert
        ticket_ids = {ticket.id for ticket in tickets}
        assert ticket_for_user_1.id in ticket_ids
        assert ticket_for_user_2.id not in ticket_ids

        for ticket in tickets:
            assert ticket.customer_id == user1.id

    finally:
        await delete_test_ticket(ticket_for_user_1.id)
        await delete_test_ticket(ticket_for_user_2.id)
        await delete_test_user(user_email_1)
        await delete_test_user(user_email_2)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_filters_tickets_by_status() -> None:
    # Arrange
    user_email = f"user{uuid4()}@example.com"
    user_password = "strong-password"
    user = await create_test_user(
        email=user_email,
        password=user_password,
    )

    ticket1 = await create_test_ticket(
        title="test-title-1",
        description="test-description-1",
        status=TicketStatus.OPEN,
        customer_id=user.id,
    )

    ticket2 = await create_test_ticket(
        title="test-title-2",
        description="test-description-2",
        status=TicketStatus.RESOLVED,
        customer_id=user.id,
    )

    try:
        async with async_session_factory() as session:
            # Act
            repository = TicketRepository(session)
            tickets = await repository.list(
                customer_id=user.id,
                assignee_id=None,
                include_unassigned=False,
                status=TicketStatus.OPEN,
                priority=None,
                offset=0,
                limit=100,
            )

        # Assert
        ticket_ids = {ticket.id for ticket in tickets}
        assert ticket1.id in ticket_ids
        assert ticket2.id not in ticket_ids

    finally:
        await delete_test_ticket(ticket1.id)
        await delete_test_ticket(ticket2.id)
        await delete_test_user(user_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_filters_tickets_by_priority() -> None:
    # Arrange
    user_email = f"user{uuid4()}@example.com"
    user_password = "strong-password"
    user = await create_test_user(
        email=user_email,
        password=user_password,
    )

    ticket1 = await create_test_ticket(
        title="test-title-1",
        description="test-description-1",
        priority=TicketPriority.HIGH,
        customer_id=user.id,
    )

    ticket2 = await create_test_ticket(
        title="test-title-2",
        description="test-description-2",
        priority=TicketPriority.LOW,
        customer_id=user.id,
    )

    try:
        async with async_session_factory() as session:
            # Act
            repository = TicketRepository(session)
            tickets = await repository.list(
                customer_id=user.id,
                assignee_id=None,
                include_unassigned=False,
                status=None,
                priority=TicketPriority.HIGH,
                offset=0,
                limit=100,
            )

        # Assert
        ticket_ids = {ticket.id for ticket in tickets}
        assert ticket1.id in ticket_ids
        assert ticket2.id not in ticket_ids

    finally:
        await delete_test_ticket(ticket1.id)
        await delete_test_ticket(ticket2.id)
        await delete_test_user(user_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_returns_assigned_and_unassigned_tickets_for_agent() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    first_agent = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    second_agent = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    first_ticket = await create_test_ticket(
        title="test-title-1",
        description="test-description-1",
        customer_id=customer.id,
        assignee_id=first_agent.id,
    )

    second_ticket = await create_test_ticket(
        title="test-title-2",
        description="test-description-2",
        customer_id=customer.id,
        assignee_id=second_agent.id,
    )

    unassigned_ticket = await create_test_ticket(
        title="test-title-unassigned",
        description="test-description-unassigned",
        customer_id=customer.id,
    )

    try:
        async with async_session_factory() as session:
            # Act
            repository = TicketRepository(session)
            tickets = await repository.list(
                customer_id=None,
                assignee_id=first_agent.id,
                include_unassigned=True,
                status=None,
                priority=None,
                offset=0,
                limit=100,
            )

        # Assert
        ticket_ids = {ticket.id for ticket in tickets}
        assert first_ticket.id in ticket_ids
        assert second_ticket.id not in ticket_ids
        assert unassigned_ticket.id in ticket_ids

    finally:
        await delete_test_ticket(first_ticket.id)
        await delete_test_ticket(second_ticket.id)
        await delete_test_ticket(unassigned_ticket.id)
        await delete_test_user(first_agent.email)
        await delete_test_user(second_agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_returns_assigned_tickets_when_unassigned_excluded() -> None:
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

    assigned_ticket = await create_test_ticket(
        title="test-title-assigned",
        description="test-description-assigned",
        customer_id=customer.id,
        assignee_id=agent.id,
    )

    unassigned_ticket = await create_test_ticket(
        title="test-title-unassigned",
        description="test-description-unassigned",
        customer_id=customer.id,
    )

    try:
        async with async_session_factory() as session:
            # Act
            repository = TicketRepository(session)
            tickets = await repository.list(
                customer_id=None,
                assignee_id=agent.id,
                include_unassigned=False,
                status=None,
                priority=None,
                offset=0,
                limit=100,
            )

        # Assert
        ticket_ids = {ticket.id for ticket in tickets}
        assert assigned_ticket.id in ticket_ids
        assert unassigned_ticket.id not in ticket_ids

    finally:
        await delete_test_ticket(assigned_ticket.id)
        await delete_test_ticket(unassigned_ticket.id)
        await delete_test_user(agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_applies_offset_and_limit() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
    )

    first_ticket = await create_test_ticket(
        title="test-title-1",
        description="test-description-1",
        customer_id=customer.id,
    )

    second_ticket = await create_test_ticket(
        title="test-title-2",
        description="test-description-2",
        customer_id=customer.id,
    )

    third_ticket = await create_test_ticket(
        title="test-title-3",
        description="test-description-3",
        customer_id=customer.id,
    )

    try:
        async with async_session_factory() as session:
            # Act
            repository = TicketRepository(session)

            first_page = await repository.list(
                customer_id=customer.id,
                assignee_id=None,
                include_unassigned=False,
                status=None,
                priority=None,
                offset=0,
                limit=2,
            )

            second_page = await repository.list(
                customer_id=customer.id,
                assignee_id=None,
                include_unassigned=False,
                status=None,
                priority=None,
                offset=2,
                limit=2,
            )

        # Assert
        first_page_ids = {ticket.id for ticket in first_page}
        second_page_ids = {ticket.id for ticket in second_page}

        all_created_ids = {
            first_ticket.id,
            second_ticket.id,
            third_ticket.id,
        }

        assert len(first_page) == 2
        assert len(second_page) == 1
        assert first_page_ids.isdisjoint(second_page_ids)
        assert first_page_ids | second_page_ids == all_created_ids

    finally:
        await delete_test_ticket(first_ticket.id)
        await delete_test_ticket(second_ticket.id)
        await delete_test_ticket(third_ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_orders_tickets_from_newest_to_oldest() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
    )

    first_ticket = await create_test_ticket(
        title="test-title-1",
        description="test-description-1",
        customer_id=customer.id,
    )

    second_ticket = await create_test_ticket(
        title="test-title-2",
        description="test-description-2",
        customer_id=customer.id,
    )

    third_ticket = await create_test_ticket(
        title="test-title-3",
        description="test-description-3",
        customer_id=customer.id,
    )

    try:
        async with async_session_factory() as session:
            # Act
            repository = TicketRepository(session)

            tickets = await repository.list(
                customer_id=customer.id,
                assignee_id=None,
                include_unassigned=False,
                status=None,
                priority=None,
                offset=0,
                limit=3,
            )

        # Assert
        assert tickets == sorted(
            tickets,
            key=lambda ticket: ticket.created_at,
            reverse=True,
        )

    finally:
        await delete_test_ticket(first_ticket.id)
        await delete_test_ticket(second_ticket.id)
        await delete_test_ticket(third_ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_count_returns_filtered_ticket_count() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"user-{uuid4()}@example.com",
        password="strong-password",
    )

    first_ticket = await create_test_ticket(
        title="test-title-1",
        description="test-description-1",
        customer_id=customer.id,
        status=TicketStatus.OPEN,
    )

    second_ticket = await create_test_ticket(
        title="test-title-2",
        description="test-description-2",
        customer_id=customer.id,
        status=TicketStatus.OPEN,
    )

    third_ticket = await create_test_ticket(
        title="test-title-3",
        description="test-description-3",
        customer_id=customer.id,
        status=TicketStatus.RESOLVED,
    )

    try:
        async with async_session_factory() as session:
            # Act
            repository = TicketRepository(session)

            total = await repository.count(
                customer_id=customer.id,
                assignee_id=None,
                include_unassigned=False,
                status=TicketStatus.OPEN,
                priority=None,
            )

        # Assert
        assert total == 2

    finally:
        await delete_test_ticket(first_ticket.id)
        await delete_test_ticket(second_ticket.id)
        await delete_test_ticket(third_ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_by_id_returns_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )

    try:
        async with async_session_factory() as session:
            # Act
            repository = TicketRepository(session)

            found_ticket = await repository.get_by_id(ticket.id)

        # Assert
        assert found_ticket is not None
        assert ticket.id == found_ticket.id
        assert ticket.customer_id == found_ticket.customer_id
        assert ticket.title == found_ticket.title

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_by_id_returns_none_for_unknown_ticket() -> None:
    # Arrange
    unknown_ticket_id = uuid4()

    async with async_session_factory() as session:
        # Act
        repository = TicketRepository(session)
        found_ticket = await repository.get_by_id(unknown_ticket_id)

    # Assert
    assert found_ticket is None


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_by_id_for_update_returns_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    ticket = await create_test_ticket(
        title="test-ticket",
        description="test-description",
        customer_id=customer.id,
    )

    try:
        async with async_session_factory() as session, session.begin():
            # Act
            repository = TicketRepository(session)
            found_ticket = await repository.get_by_id_for_update(ticket.id)

        # Assert
        assert found_ticket is not None
        assert ticket.id == found_ticket.id
        assert ticket.customer_id == found_ticket.customer_id

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_by_id_for_update_returns_none_for_unknown_ticket() -> None:
    # Arrange
    unknown_ticket_id = uuid4()

    async with async_session_factory() as session, session.begin():
        # Act
        repository = TicketRepository(session)

        found_ticket = await repository.get_by_id_for_update(unknown_ticket_id)

    # Assert
    assert found_ticket is None
