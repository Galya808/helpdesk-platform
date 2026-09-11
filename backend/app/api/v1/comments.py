from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession
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
from app.comments.use_cases import (
    AddTicketComment,
    ListTicketComments,
)
from app.tickets.exceptions import TicketNotFoundError
from app.tickets.repository import TicketRepository

router = APIRouter(
    prefix="/tickets/{ticket_id}/comments",
    tags=["comments"],
)

CommentQuery = Annotated[
    CommentListQuery,
    Depends(),
]


@router.post(
    "",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    ticket_id: UUID,
    data: CommentCreate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> CommentRead:
    ticket_repository = TicketRepository(session)
    comment_repository = TicketCommentRepository(session)
    use_case = AddTicketComment(
        ticket_repository=ticket_repository,
        comment_repository=comment_repository,
    )

    try:
        created_comment = await use_case.execute(
            ticket_id=ticket_id,
            data=data,
            current_user=current_user,
        )

        await session.commit()

        return created_comment

    except TicketNotFoundError as error:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        ) from error

    except CommentCreationForbiddenError as error:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Comment creation is forbidden",
        ) from error

    except TicketClosedForCommentsError as error:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Comments cannot be added to a closed ticket",
        ) from error


@router.get(
    "",
    response_model=CommentPage,
    status_code=status.HTTP_200_OK,
)
async def get_comments(
    ticket_id: UUID,
    query: CommentQuery,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> CommentPage:
    ticket_repository = TicketRepository(session)
    comment_repository = TicketCommentRepository(session)
    use_case = ListTicketComments(
        ticket_repository=ticket_repository,
        comment_repository=comment_repository,
    )

    try:
        result = await use_case.execute(
            ticket_id=ticket_id,
            query=query,
            current_user=current_user,
        )

    except TicketNotFoundError as error:
        raise HTTPException(
            detail="Ticket not found",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from error

    except CommentViewingForbiddenError as error:
        raise HTTPException(
            detail="Comment viewing is forbidden",
            status_code=status.HTTP_403_FORBIDDEN,
        ) from error

    return result
