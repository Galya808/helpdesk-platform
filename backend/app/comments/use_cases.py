from uuid import UUID

from app.comments.exceptions import (
    CommentCreationForbiddenError,
    CommentViewingForbiddenError,
    TicketClosedForCommentsError,
)
from app.comments.repository import TicketCommentRepository
from app.comments.schemas import (
    CommentCreate,
    CommentListQuery,
    CommentPage,
    CommentRead,
)
from app.tickets.exceptions import TicketNotFoundError
from app.tickets.model import Ticket, TicketStatus
from app.tickets.repository import TicketRepository
from app.users.model import User, UserRole


def _can_access_ticket_comments(
    ticket: Ticket,
    current_user: User,
) -> bool:
    return (
        current_user.role is UserRole.ADMIN
        or (
            current_user.role is UserRole.CUSTOMER
            and ticket.customer_id == current_user.id
        )
        or (
            current_user.role is UserRole.SUPPORT_AGENT
            and ticket.assignee_id == current_user.id
        )
    )


class AddTicketComment:
    def __init__(
        self,
        ticket_repository: TicketRepository,
        comment_repository: TicketCommentRepository,
    ) -> None:
        self.ticket_repository = ticket_repository
        self.comment_repository = comment_repository

    async def execute(
        self,
        *,
        ticket_id: UUID,
        data: CommentCreate,
        current_user: User,
    ) -> CommentRead:
        if current_user.is_blocked:
            raise CommentCreationForbiddenError

        ticket = await self.ticket_repository.get_by_id(
            ticket_id=ticket_id,
        )

        if ticket is None:
            raise TicketNotFoundError

        if not _can_access_ticket_comments(ticket, current_user):
            raise CommentCreationForbiddenError

        if ticket.status is TicketStatus.CLOSED:
            raise TicketClosedForCommentsError

        comment = await self.comment_repository.create(
            ticket_id=ticket.id,
            author_id=current_user.id,
            content=data.content,
        )

        return CommentRead.model_validate(comment)


class ListTicketComments:
    def __init__(
        self,
        ticket_repository: TicketRepository,
        comment_repository: TicketCommentRepository,
    ) -> None:
        self.ticket_repository = ticket_repository
        self.comment_repository = comment_repository

    async def execute(
        self,
        *,
        ticket_id: UUID,
        query: CommentListQuery,
        current_user: User,
    ) -> CommentPage:
        if current_user.is_blocked:
            raise CommentViewingForbiddenError

        ticket = await self.ticket_repository.get_by_id(
            ticket_id=ticket_id,
        )

        if ticket is None:
            raise TicketNotFoundError

        if not _can_access_ticket_comments(ticket, current_user):
            raise CommentViewingForbiddenError

        comments = await self.comment_repository.list_by_ticket(
            ticket_id=ticket.id,
            offset=query.offset,
            limit=query.page_size,
        )

        total = await self.comment_repository.count_by_ticket(
            ticket_id=ticket.id,
        )

        return CommentPage(
            items=[CommentRead.model_validate(comment) for comment in comments],
            page=query.page,
            page_size=query.page_size,
            total=total,
        )
