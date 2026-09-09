from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.comments.exceptions import (
    CommentCreationForbiddenError,
    TicketClosedForCommentsError,
)
from app.comments.model import TicketComment
from app.comments.repository import TicketCommentRepository
from app.comments.schemas import CommentCreate
from app.comments.use_cases import AddTicketComment
from app.tickets.exceptions import TicketNotFoundError
from app.tickets.model import Ticket, TicketPriority, TicketStatus
from app.tickets.repository import TicketRepository
from app.users.model import User, UserRole


def make_user(
    role: UserRole,
    *,
    is_blocked: bool = False,
) -> User:
    user_id = uuid4()

    return User(
        id=user_id,
        email=f"{role.value}-{user_id}@example.com",
        hashed_password="hashed-password",
        role=role,
        is_blocked=is_blocked,
    )


def make_ticket(
    *,
    customer_id: UUID,
    assignee_id: UUID | None = None,
    status: TicketStatus = TicketStatus.OPEN,
) -> Ticket:
    created_at = datetime.now(UTC)

    return Ticket(
        id=uuid4(),
        title="test-title",
        description="test-description",
        customer_id=customer_id,
        assignee_id=assignee_id,
        status=status,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=created_at,
    )


def make_comment(
    *,
    ticket_id: UUID,
    author_id: UUID,
    content: str,
) -> TicketComment:
    return TicketComment(
        id=uuid4(),
        ticket_id=ticket_id,
        author_id=author_id,
        content=content,
        created_at=datetime.now(UTC),
    )


@pytest.mark.parametrize(
    "role",
    [
        UserRole.CUSTOMER,
        UserRole.SUPPORT_AGENT,
        UserRole.ADMIN,
    ],
    ids=["customer", "assigned-agent", "admin"],
)
@pytest.mark.asyncio
async def test_authorized_user_adds_comment(
    role: UserRole,
) -> None:
    # Arrange
    current_user = make_user(role)
    customer_id = current_user.id if role is UserRole.CUSTOMER else uuid4()
    assignee_id = current_user.id if role is UserRole.SUPPORT_AGENT else None
    ticket = make_ticket(
        customer_id=customer_id,
        assignee_id=assignee_id,
    )
    data = CommentCreate(content="test-comment")
    expected_comment = make_comment(
        ticket_id=ticket.id,
        author_id=current_user.id,
        content=data.content,
    )

    ticket_repository = AsyncMock(spec=TicketRepository)
    comment_repository = AsyncMock(spec=TicketCommentRepository)
    ticket_repository.get_by_id.return_value = ticket
    comment_repository.create.return_value = expected_comment

    use_case = AddTicketComment(
        ticket_repository=ticket_repository,
        comment_repository=comment_repository,
    )

    # Act
    result = await use_case.execute(
        ticket_id=ticket.id,
        data=data,
        current_user=current_user,
    )

    # Assert
    assert result.id == expected_comment.id
    assert result.ticket_id == ticket.id
    assert result.author_id == current_user.id
    assert result.content == data.content
    assert result.created_at == expected_comment.created_at

    ticket_repository.get_by_id.assert_awaited_once_with(ticket_id=ticket.id)
    comment_repository.create.assert_awaited_once_with(
        ticket_id=ticket.id,
        author_id=current_user.id,
        content=data.content,
    )


@pytest.mark.asyncio
async def test_customer_cannot_comment_on_another_customers_ticket() -> None:
    # Arrange
    customer = make_user(UserRole.CUSTOMER)
    ticket = make_ticket(customer_id=uuid4())
    data = CommentCreate(content="test-comment")

    ticket_repository = AsyncMock(spec=TicketRepository)
    comment_repository = AsyncMock(spec=TicketCommentRepository)
    ticket_repository.get_by_id.return_value = ticket
    use_case = AddTicketComment(ticket_repository, comment_repository)

    # Act + Assert
    with pytest.raises(CommentCreationForbiddenError):
        await use_case.execute(
            ticket_id=ticket.id,
            data=data,
            current_user=customer,
        )

    ticket_repository.get_by_id.assert_awaited_once_with(ticket_id=ticket.id)
    comment_repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_unassigned_agent_cannot_comment_on_ticket() -> None:
    # Arrange
    agent = make_user(UserRole.SUPPORT_AGENT)
    ticket = make_ticket(customer_id=uuid4(), assignee_id=None)
    data = CommentCreate(content="test-comment")

    ticket_repository = AsyncMock(spec=TicketRepository)
    comment_repository = AsyncMock(spec=TicketCommentRepository)
    ticket_repository.get_by_id.return_value = ticket
    use_case = AddTicketComment(ticket_repository, comment_repository)

    # Act + Assert
    with pytest.raises(CommentCreationForbiddenError):
        await use_case.execute(
            ticket_id=ticket.id,
            data=data,
            current_user=agent,
        )

    ticket_repository.get_by_id.assert_awaited_once_with(ticket_id=ticket.id)
    comment_repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_agent_cannot_comment_on_another_agents_ticket() -> None:
    # Arrange
    agent = make_user(UserRole.SUPPORT_AGENT)
    ticket = make_ticket(customer_id=uuid4(), assignee_id=uuid4())
    data = CommentCreate(content="test-comment")

    ticket_repository = AsyncMock(spec=TicketRepository)
    comment_repository = AsyncMock(spec=TicketCommentRepository)
    ticket_repository.get_by_id.return_value = ticket
    use_case = AddTicketComment(ticket_repository, comment_repository)

    # Act + Assert
    with pytest.raises(CommentCreationForbiddenError):
        await use_case.execute(
            ticket_id=ticket.id,
            data=data,
            current_user=agent,
        )

    ticket_repository.get_by_id.assert_awaited_once_with(ticket_id=ticket.id)
    comment_repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_comment_cannot_be_added_to_closed_ticket() -> None:
    # Arrange
    customer = make_user(UserRole.CUSTOMER)
    ticket = make_ticket(
        customer_id=customer.id,
        status=TicketStatus.CLOSED,
    )
    data = CommentCreate(content="test-comment")

    ticket_repository = AsyncMock(spec=TicketRepository)
    comment_repository = AsyncMock(spec=TicketCommentRepository)
    ticket_repository.get_by_id.return_value = ticket
    use_case = AddTicketComment(ticket_repository, comment_repository)

    # Act + Assert
    with pytest.raises(TicketClosedForCommentsError):
        await use_case.execute(
            ticket_id=ticket.id,
            data=data,
            current_user=customer,
        )

    ticket_repository.get_by_id.assert_awaited_once_with(ticket_id=ticket.id)
    comment_repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_comment_cannot_be_added_to_unknown_ticket() -> None:
    # Arrange
    customer = make_user(UserRole.CUSTOMER)
    ticket_id = uuid4()
    data = CommentCreate(content="test-comment")

    ticket_repository = AsyncMock(spec=TicketRepository)
    comment_repository = AsyncMock(spec=TicketCommentRepository)
    ticket_repository.get_by_id.return_value = None
    use_case = AddTicketComment(ticket_repository, comment_repository)

    # Act + Assert
    with pytest.raises(TicketNotFoundError):
        await use_case.execute(
            ticket_id=ticket_id,
            data=data,
            current_user=customer,
        )

    ticket_repository.get_by_id.assert_awaited_once_with(ticket_id=ticket_id)
    comment_repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_blocked_user_cannot_add_comment() -> None:
    # Arrange
    customer = make_user(UserRole.CUSTOMER, is_blocked=True)
    ticket_id = uuid4()
    data = CommentCreate(content="test-comment")

    ticket_repository = AsyncMock(spec=TicketRepository)
    comment_repository = AsyncMock(spec=TicketCommentRepository)
    use_case = AddTicketComment(ticket_repository, comment_repository)

    # Act + Assert
    with pytest.raises(CommentCreationForbiddenError):
        await use_case.execute(
            ticket_id=ticket_id,
            data=data,
            current_user=customer,
        )

    ticket_repository.get_by_id.assert_not_awaited()
    comment_repository.create.assert_not_awaited()
