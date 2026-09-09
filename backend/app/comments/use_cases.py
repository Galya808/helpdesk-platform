from uuid import UUID

from app.comments.exceptions import (
    CommentCreationForbiddenError,
    TicketClosedForCommentsError,
)
from app.comments.repository import TicketCommentRepository
from app.comments.schemas import CommentCreate, CommentRead
from app.tickets.exceptions import TicketNotFoundError
from app.tickets.model import TicketStatus
from app.tickets.repository import TicketRepository
from app.users.model import User, UserRole


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

        has_access = (
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

        if not has_access:
            raise CommentCreationForbiddenError

        if ticket.status is TicketStatus.CLOSED:
            raise TicketClosedForCommentsError

        comment = await self.comment_repository.create(
            ticket_id=ticket.id,
            author_id=current_user.id,
            content=data.content,
        )

        return CommentRead.model_validate(comment)
