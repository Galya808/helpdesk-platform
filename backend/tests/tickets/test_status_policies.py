from datetime import UTC, datetime
from uuid import uuid4

from app.tickets.model import Ticket, TicketPriority, TicketStatus
from app.tickets.status_policies import (
    CustomerTicketStatusPolicy,
    SupportAgentTicketStatusPolicy,
)
from app.users.model import User, UserRole


def test_customer_has_access_to_own_tickets() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
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

    policy = CustomerTicketStatusPolicy()

    # Act
    result = policy.has_access(ticket, customer)

    # Assert
    assert result is True


def test_customer_has_no_access_another_tickets() -> None:
    # Arrange
    owner = User(
        id=uuid4(),
        email="owner@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        customer_id=owner.id,
        assignee_id=None,
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    policy = CustomerTicketStatusPolicy()

    # Act
    result = policy.has_access(ticket, customer)

    # Assert
    assert result is False


def test_open_status_returns_closed_status() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
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

    policy = CustomerTicketStatusPolicy()

    # Act
    result = policy.allowed_statuses(ticket, customer)

    # Assert
    assert result == {TicketStatus.CLOSED}


def test_resolved_status_returns_closed_and_in_progress_status() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
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
        status=TicketStatus.RESOLVED,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    policy = CustomerTicketStatusPolicy()

    # Act
    result = policy.allowed_statuses(ticket, customer)

    # Assert
    assert result == {
        TicketStatus.CLOSED,
        TicketStatus.IN_PROGRESS,
    }


def test_in_progress_status_returns_no_status() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
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
        status=TicketStatus.IN_PROGRESS,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    policy = CustomerTicketStatusPolicy()

    # Act
    result = policy.allowed_statuses(ticket, customer)

    # Assert
    assert result == set()


def test_closed_status_returns_no_status() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
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
        status=TicketStatus.CLOSED,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    policy = CustomerTicketStatusPolicy()

    # Act
    result = policy.allowed_statuses(ticket, customer)

    # Assert
    assert result == set()


def test_agent_has_access_to_own_assigned_tickets() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    agent = User(
        id=uuid4(),
        email="agent@example.com",
        hashed_password="hashed-password",
        role=UserRole.SUPPORT_AGENT,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=agent.id,
        status=TicketStatus.CLOSED,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    policy = SupportAgentTicketStatusPolicy()

    # Act
    result = policy.has_access(ticket, agent)

    # Assert
    assert result is True


def test_agent_has_no_access_to_unassigned_tickets() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    agent = User(
        id=uuid4(),
        email="agent@example.com",
        hashed_password="hashed-password",
        role=UserRole.SUPPORT_AGENT,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=None,
        status=TicketStatus.CLOSED,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    policy = SupportAgentTicketStatusPolicy()

    # Act
    result = policy.has_access(ticket, agent)

    # Assert
    assert result is False


def test_agent_has_no_access_to_ticket_assigned_to_another_agent() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    owner_agent = User(
        id=uuid4(),
        email="owner_agent@example.com",
        hashed_password="hashed-password",
        role=UserRole.SUPPORT_AGENT,
    )

    current_agent = User(
        id=uuid4(),
        email="current_agent@example.com",
        hashed_password="hashed-password",
        role=UserRole.SUPPORT_AGENT,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=owner_agent.id,
        status=TicketStatus.CLOSED,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    policy = SupportAgentTicketStatusPolicy()

    # Act
    result = policy.has_access(ticket, current_agent)

    # Assert
    assert result is False


def test_in_progress_for_agent_status_returns_only_resolved() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    agent = User(
        id=uuid4(),
        email="agent@example.com",
        hashed_password="hashed-password",
        role=UserRole.SUPPORT_AGENT,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=agent.id,
        status=TicketStatus.IN_PROGRESS,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    policy = SupportAgentTicketStatusPolicy()

    # Act
    result = policy.allowed_statuses(ticket, agent)

    # Assert
    assert result == {
        TicketStatus.RESOLVED,
    }


def test_resolved_for_agent_status_returns_only_closed() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    agent = User(
        id=uuid4(),
        email="agent@example.com",
        hashed_password="hashed-password",
        role=UserRole.SUPPORT_AGENT,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=agent.id,
        status=TicketStatus.RESOLVED,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    policy = SupportAgentTicketStatusPolicy()

    # Act
    result = policy.allowed_statuses(ticket, agent)

    # Assert
    assert result == {
        TicketStatus.CLOSED,
    }


def test_open_for_agent_status_returns_no_status() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    agent = User(
        id=uuid4(),
        email="agent@example.com",
        hashed_password="hashed-password",
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

    policy = SupportAgentTicketStatusPolicy()

    # Act
    result = policy.allowed_statuses(ticket, agent)

    # Assert
    assert result == set()


def test_closed_for_agent_status_returns_no_status() -> None:
    # Arrange
    customer = User(
        id=uuid4(),
        email="customer@example.com",
        hashed_password="hashed-password",
        role=UserRole.CUSTOMER,
    )

    agent = User(
        id=uuid4(),
        email="agent@example.com",
        hashed_password="hashed-password",
        role=UserRole.SUPPORT_AGENT,
    )

    created_at = datetime.now(UTC)

    ticket = Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=agent.id,
        status=TicketStatus.CLOSED,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )

    policy = SupportAgentTicketStatusPolicy()

    # Act
    result = policy.allowed_statuses(ticket, agent)

    # Assert
    assert result == set()
