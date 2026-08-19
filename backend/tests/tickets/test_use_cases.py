from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.tickets.exceptions import (
    TicketAlreadyAssignedError,
    TicketAssignmentForbiddenError,
    TicketCreationForbiddenError,
    TicketNotAssignableError,
    TicketNotFoundError,
)
from app.tickets.model import Ticket, TicketPriority, TicketStatus
from app.tickets.repository import TicketRepository
from app.tickets.schemas import TicketCreate, TicketListQuery
from app.tickets.use_cases import (
    AssignTicket,
    CreateTicket,
    GetTicket,
    ListTickets,
)
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


@pytest.mark.asyncio
async def test_customer_lists_only_own_tickets() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="user@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    created_at = datetime.now(UTC)

    first_ticket = Ticket(
        id=uuid4(),
        title="test-title-1",
        description="test-description-1",
        customer_id=customer.id,
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        assignee_id=None,
        created_at=created_at,
        updated_at=created_at,
    )

    second_ticket = Ticket(
        id=uuid4(),
        title="test-title-2",
        description="test-description-2",
        customer_id=customer.id,
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        assignee_id=None,
        created_at=created_at,
        updated_at=created_at,
    )

    repository = AsyncMock(spec=TicketRepository)
    repository.list.return_value = [first_ticket, second_ticket]
    repository.count.return_value = 2

    use_case = ListTickets(repository)
    query = TicketListQuery()

    # Act
    result = await use_case.execute(
        query,
        customer,
    )

    # Assert
    assert result.page == 1
    assert result.page_size == 20
    assert result.total == 2
    assert result.pages == 1
    assert [ticket.id for ticket in result.items] == [
        first_ticket.id,
        second_ticket.id,
    ]

    repository.list.assert_awaited_once_with(
        customer_id=customer.id,
        assignee_id=None,
        include_unassigned=False,
        status=None,
        priority=None,
        offset=0,
        limit=20,
    )

    repository.count.assert_awaited_once_with(
        customer_id=customer.id,
        assignee_id=None,
        include_unassigned=False,
        status=None,
        priority=None,
    )


@pytest.mark.asyncio
async def test_support_agent_lists_assigned_and_unassigned_tickets() -> None:
    # Arrange
    created_at = datetime.now(UTC)

    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="customer-hashed-password",
        role=UserRole.CUSTOMER,
    )

    agent = User(
        id=uuid4(),
        email="agent@example.com",
        hashed_password="agent-hashed-password",
        role=UserRole.SUPPORT_AGENT,
    )

    assigned_ticket = Ticket(
        id=uuid4(),
        title="test-title-assigned",
        description="test-description-assigned",
        customer_id=customer.id,
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        assignee_id=agent.id,
        created_at=created_at,
        updated_at=created_at,
    )

    unassigned_ticket = Ticket(
        id=uuid4(),
        title="test-title-unassigned",
        description="test-description-unassigned",
        customer_id=customer.id,
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        assignee_id=None,
        created_at=created_at,
        updated_at=created_at,
    )

    repository = AsyncMock(spec=TicketRepository)
    repository.list.return_value = [
        assigned_ticket,
        unassigned_ticket,
    ]
    repository.count.return_value = 2

    use_case = ListTickets(repository)

    query = TicketListQuery()

    # Act
    result = await use_case.execute(
        query=query,
        current_user=agent,
    )

    # Assert
    assert result.page == 1
    assert result.page_size == 20
    assert result.total == 2
    assert result.pages == 1
    assert [ticket.id for ticket in result.items] == [
        assigned_ticket.id,
        unassigned_ticket.id,
    ]

    repository.list.assert_awaited_once_with(
        customer_id=None,
        assignee_id=agent.id,
        include_unassigned=True,
        status=None,
        priority=None,
        offset=0,
        limit=20,
    )

    repository.count.assert_awaited_once_with(
        customer_id=None,
        assignee_id=agent.id,
        include_unassigned=True,
        status=None,
        priority=None,
    )


@pytest.mark.asyncio
async def test_admin_lists_all_tickets() -> None:
    # Arrange
    created_at = datetime.now(UTC)

    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="customer-hashed-password",
        role=UserRole.CUSTOMER,
    )

    admin = User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password="admin-hashed-password",
        role=UserRole.ADMIN,
    )

    first_ticket = Ticket(
        id=uuid4(),
        title="test-title-first",
        description="test-description-first",
        customer_id=customer.id,
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        assignee_id=None,
        created_at=created_at,
        updated_at=created_at,
    )

    second_ticket = Ticket(
        id=uuid4(),
        title="test-title-second",
        description="test-description-second",
        customer_id=customer.id,
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        assignee_id=None,
        created_at=created_at,
        updated_at=created_at,
    )

    repository = AsyncMock(spec=TicketRepository)
    repository.list.return_value = [
        first_ticket,
        second_ticket,
    ]
    repository.count.return_value = 2

    use_case = ListTickets(repository)
    query = TicketListQuery()

    # Act
    result = await use_case.execute(
        query=query,
        current_user=admin,
    )

    # Assert
    assert result.page == 1
    assert result.page_size == 20
    assert result.total == 2
    assert result.pages == 1
    assert [ticket.id for ticket in result.items] == [
        first_ticket.id,
        second_ticket.id,
    ]

    repository.list.assert_awaited_once_with(
        customer_id=None,
        assignee_id=None,
        include_unassigned=False,
        status=None,
        priority=None,
        offset=0,
        limit=20,
    )

    repository.count.assert_awaited_once_with(
        customer_id=None,
        assignee_id=None,
        include_unassigned=False,
        status=None,
        priority=None,
    )


@pytest.mark.asyncio
async def test_list_tickets_passes_filters_and_pagination() -> None:
    # Arrange
    admin = User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password="admin-hashed-password",
        role=UserRole.ADMIN,
    )

    repository = AsyncMock(spec=TicketRepository)
    repository.list.return_value = []
    repository.count.return_value = 0

    use_case = ListTickets(repository)

    query = TicketListQuery(
        page=3,
        page_size=10,
        status=TicketStatus.OPEN,
        priority=TicketPriority.HIGH,
    )

    # Act
    result = await use_case.execute(
        query=query,
        current_user=admin,
    )

    # Assert
    assert result.page == query.page
    assert result.page_size == query.page_size
    assert result.total == 0
    assert result.pages == 0

    assert result.items == []

    repository.list.assert_awaited_once_with(
        customer_id=None,
        assignee_id=None,
        include_unassigned=False,
        status=TicketStatus.OPEN,
        priority=TicketPriority.HIGH,
        offset=20,
        limit=10,
    )

    repository.count.assert_awaited_once_with(
        customer_id=None,
        assignee_id=None,
        include_unassigned=False,
        status=TicketStatus.OPEN,
        priority=TicketPriority.HIGH,
    )


@pytest.mark.asyncio
async def test_customer_gets_own_ticket() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email=f"customer-{uuid4()}@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=None,
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    repository = AsyncMock(spec=TicketRepository)
    repository.get_by_id.return_value = ticket

    use_case = GetTicket(repository)

    # Act
    found_ticket = await use_case.execute(
        ticket_id=ticket.id,
        current_user=customer,
    )

    # Assert
    assert ticket.id == found_ticket.id
    assert ticket.customer_id == found_ticket.customer_id

    repository.get_by_id.assert_awaited_once_with(ticket.id)


@pytest.mark.asyncio
async def test_customer_cannot_get_another_customers_ticket() -> None:
    # Arrange
    ticket_owner = User(
        id=uuid4(),
        email=f"customer-{uuid4()}@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    customer = User(
        id=uuid4(),
        email=f"customer-{uuid4()}@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        customer_id=ticket_owner.id,
        assignee_id=None,
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    repository = AsyncMock(spec=TicketRepository)
    repository.get_by_id.return_value = ticket

    use_case = GetTicket(repository)

    # Act + Assert
    with pytest.raises(TicketNotFoundError):
        await use_case.execute(ticket.id, customer)

    repository.get_by_id.assert_awaited_once_with(ticket.id)


@pytest.mark.asyncio
async def test_support_agent_gets_unassigned_ticket() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email=f"customer-{uuid4()}@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    agent = User(
        id=uuid4(),
        email=f"agent-{uuid4()}@example.com",
        hashed_password="hashed_password",
        role=UserRole.SUPPORT_AGENT,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=None,
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    repository = AsyncMock(spec=TicketRepository)
    repository.get_by_id.return_value = ticket

    use_case = GetTicket(repository)

    # Act
    found_ticket = await use_case.execute(ticket.id, agent)

    # Assert
    assert ticket.id == found_ticket.id
    assert ticket.customer_id == found_ticket.customer_id
    assert found_ticket.assignee_id is None

    repository.get_by_id.assert_awaited_once_with(ticket.id)


@pytest.mark.asyncio
async def test_support_agent_gets_assigned_ticket() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email=f"customer-{uuid4()}@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    agent = User(
        id=uuid4(),
        email=f"agent-{uuid4()}@example.com",
        hashed_password="hashed_password",
        role=UserRole.SUPPORT_AGENT,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=agent.id,
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    repository = AsyncMock(spec=TicketRepository)
    repository.get_by_id.return_value = ticket

    use_case = GetTicket(repository)

    # Act
    found_ticket = await use_case.execute(ticket.id, agent)

    # Assert
    assert ticket.id == found_ticket.id
    assert ticket.customer_id == found_ticket.customer_id
    assert found_ticket.assignee_id == agent.id

    repository.get_by_id.assert_awaited_once_with(ticket.id)


@pytest.mark.asyncio
async def test_support_agent_cannot_get_another_agents_ticket() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email=f"customer-{uuid4()}@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    assigned_agent = User(
        id=uuid4(),
        email=f"agent-{uuid4()}@example.com",
        hashed_password="hashed_password",
        role=UserRole.SUPPORT_AGENT,
    )

    current_agent = User(
        id=uuid4(),
        email=f"agent-{uuid4()}@example.com",
        hashed_password="hashed_password",
        role=UserRole.SUPPORT_AGENT,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=assigned_agent.id,
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    repository = AsyncMock(spec=TicketRepository)
    repository.get_by_id.return_value = ticket

    use_case = GetTicket(repository)

    # Act + Assert
    with pytest.raises(TicketNotFoundError):
        await use_case.execute(ticket.id, current_agent)

    repository.get_by_id.assert_awaited_once_with(ticket.id)


@pytest.mark.asyncio
async def test_admin_gets_any_ticket() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email=f"customer-{uuid4()}@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    admin = User(
        id=uuid4(),
        email=f"agent-{uuid4()}@example.com",
        hashed_password="hashed_password",
        role=UserRole.ADMIN,
    )

    agent = User(
        id=uuid4(),
        email=f"agent-{uuid4()}@example.com",
        hashed_password="hashed_password",
        role=UserRole.SUPPORT_AGENT,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=agent.id,
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    repository = AsyncMock(spec=TicketRepository)
    repository.get_by_id.return_value = ticket

    use_case = GetTicket(repository)

    # Act
    found_ticket = await use_case.execute(ticket.id, admin)

    # Assert
    assert found_ticket.id == ticket.id
    assert found_ticket.customer_id == ticket.customer_id
    assert found_ticket.assignee_id == agent.id

    repository.get_by_id.assert_awaited_once_with(ticket.id)


@pytest.mark.asyncio
async def test_get_ticket_raises_for_unknown_ticket() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email=f"customer-{uuid4()}@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    unknown_ticket_id = uuid4()

    repository = AsyncMock(spec=TicketRepository)
    repository.get_by_id.return_value = None

    use_case = GetTicket(repository)

    # Act + Assert
    with pytest.raises(TicketNotFoundError):
        await use_case.execute(unknown_ticket_id, customer)

    repository.get_by_id.assert_awaited_once_with(unknown_ticket_id)


@pytest.mark.asyncio
async def test_support_agent_assigns_open_ticket() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
        is_blocked=False,
    )

    agent = User(
        id=uuid4(),
        email="agent@example.com",
        hashed_password="hashed-password",
        role=UserRole.SUPPORT_AGENT,
        is_blocked=False,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        customer_id=customer.id,
        assignee_id=None,
        created_at=created_at,
        updated_at=created_at,
    )

    repository = AsyncMock(spec=TicketRepository)
    use_case = AssignTicket(repository)

    repository.get_by_id_for_update.return_value = ticket
    repository.save.return_value = ticket

    # Act
    found_ticket = await use_case.execute(ticket.id, agent)

    # Assert
    assert ticket.id == found_ticket.id
    assert ticket.customer_id == found_ticket.customer_id
    assert ticket.assignee_id == agent.id
    assert ticket.status is TicketStatus.IN_PROGRESS
    assert found_ticket.assignee_id == agent.id
    assert found_ticket.status is TicketStatus.IN_PROGRESS

    repository.get_by_id_for_update.assert_awaited_once_with(ticket.id)
    repository.save.assert_awaited_once_with(ticket)


@pytest.mark.asyncio
async def test_customer_cannot_assign_ticket() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
        is_blocked=False,
    )

    ticket_id = uuid4()

    repository = AsyncMock(spec=TicketRepository)
    use_case = AssignTicket(repository)

    # Act + Assert
    with pytest.raises(TicketAssignmentForbiddenError):
        await use_case.execute(ticket_id, customer)

    repository.get_by_id_for_update.assert_not_awaited()
    repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_admin_cannot_assign_ticket() -> None:
    # Arrange
    admin = User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password="hashed-password",
        role=UserRole.ADMIN,
        is_blocked=False,
    )

    ticket_id = uuid4()

    repository = AsyncMock(spec=TicketRepository)
    use_case = AssignTicket(repository)

    # Act + Assert
    with pytest.raises(TicketAssignmentForbiddenError):
        await use_case.execute(ticket_id, admin)

    repository.get_by_id_for_update.assert_not_awaited()
    repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_blocked_agent_cannot_assign_ticket() -> None:
    # Arrange
    agent = User(
        id=uuid4(),
        email="agent@example.com",
        hashed_password="hashed-password",
        role=UserRole.SUPPORT_AGENT,
        is_blocked=True,
    )

    ticket_id = uuid4()

    repository = AsyncMock(spec=TicketRepository)
    use_case = AssignTicket(repository)

    # Act + Assert
    with pytest.raises(TicketAssignmentForbiddenError):
        await use_case.execute(ticket_id, agent)

    repository.get_by_id_for_update.assert_not_awaited()
    repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_unknown_ticket_raises_not_found() -> None:
    # Arrange
    agent = User(
        id=uuid4(),
        email="agent@example.com",
        hashed_password="hashed-password",
        role=UserRole.SUPPORT_AGENT,
        is_blocked=False,
    )

    unknown_ticket_id = uuid4()

    repository = AsyncMock(spec=TicketRepository)
    use_case = AssignTicket(repository)

    repository.get_by_id_for_update.return_value = None

    # Act + Assert
    with pytest.raises(TicketNotFoundError):
        await use_case.execute(unknown_ticket_id, agent)

    repository.get_by_id_for_update.assert_awaited_once_with(unknown_ticket_id)
    repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_assigned_ticket_raises_conflict() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
        is_blocked=False,
    )

    assigned_agent = User(
        id=uuid4(),
        email="assigned-agent@example.com",
        hashed_password="hashed-password",
        role=UserRole.SUPPORT_AGENT,
        is_blocked=False,
    )

    current_agent = User(
        id=uuid4(),
        email="current-agent@example.com",
        hashed_password="hashed-password",
        role=UserRole.SUPPORT_AGENT,
        is_blocked=False,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        customer_id=customer.id,
        assignee_id=assigned_agent.id,
        created_at=created_at,
        updated_at=created_at,
    )

    repository = AsyncMock(spec=TicketRepository)
    use_case = AssignTicket(repository)

    repository.get_by_id_for_update.return_value = ticket

    # Act + Assert
    with pytest.raises(TicketAlreadyAssignedError):
        await use_case.execute(ticket.id, current_agent)

    repository.get_by_id_for_update.assert_awaited_once_with(
        ticket.id,
    )
    repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_non_open_ticket_raises_conflict() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
        is_blocked=False,
    )

    agent = User(
        id=uuid4(),
        email="current-agent@example.com",
        hashed_password="hashed-password",
        role=UserRole.SUPPORT_AGENT,
        is_blocked=False,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        status=TicketStatus.IN_PROGRESS,
        priority=TicketPriority.MEDIUM,
        customer_id=customer.id,
        assignee_id=None,
        created_at=created_at,
        updated_at=created_at,
    )

    repository = AsyncMock(spec=TicketRepository)
    use_case = AssignTicket(repository)

    repository.get_by_id_for_update.return_value = ticket

    # Act + Assert
    with pytest.raises(TicketNotAssignableError):
        await use_case.execute(ticket.id, agent)

    repository.get_by_id_for_update.assert_awaited_once_with(
        ticket.id,
    )
    repository.save.assert_not_awaited()
