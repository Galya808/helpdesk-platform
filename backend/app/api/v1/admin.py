from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.tickets.exceptions import (
    ClosedTicketReassignmentError,
    InvalidTicketAssigneeError,
    TicketNotFoundError,
    TicketReassignmentForbiddenError,
)
from app.tickets.repository import TicketRepository
from app.tickets.schemas import TicketAssigneeUpdate, TicketRead
from app.tickets.use_cases import ReassignTicket
from app.users.exceptions import (
    UserManagementForbiddenError,
    UserNotFoundError,
    UserSelfManagementForbiddenError,
)
from app.users.repository import UserRepository
from app.users.schemas import (
    UserBlockedUpdate,
    UserListQuery,
    UserPage,
    UserRead,
    UserRoleUpdate,
)
from app.users.use_cases import ChangeUserBlockedStatus, ChangeUserRole, ListUsers

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

UserQuery = Annotated[
    UserListQuery,
    Depends(),
]


@router.get(
    "/users",
    response_model=UserPage,
)
async def list_users(
    query: UserQuery,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> UserPage:
    try:
        repository = UserRepository(session)
        use_case = ListUsers(repository)

        result = await use_case.execute(
            query=query,
            current_user=current_user,
        )

        return result

    except UserManagementForbiddenError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User management is restricted to administrators",
        ) from error


@router.patch("/users/{user_id}/role", response_model=UserRead)
async def change_user_role(
    user_id: UUID,
    data: UserRoleUpdate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> UserRead:
    repository = UserRepository(session)
    use_case = ChangeUserRole(repository)

    try:
        updated_user = await use_case.execute(
            user_id=user_id,
            data=data,
            current_user=current_user,
        )
        await session.commit()
        return updated_user
    except UserManagementForbiddenError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User management is restricted to administrators",
        ) from error
    except UserSelfManagementForbiddenError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrators cannot change their own account",
        ) from error
    except UserNotFoundError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from error


@router.patch("/users/{user_id}/blocked", response_model=UserRead)
async def change_user_blocked_status(
    user_id: UUID,
    data: UserBlockedUpdate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> UserRead:
    repository = UserRepository(session)
    use_case = ChangeUserBlockedStatus(repository)

    try:
        updated_user = await use_case.execute(
            user_id=user_id,
            data=data,
            current_user=current_user,
        )
        await session.commit()
        return updated_user
    except UserManagementForbiddenError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User management is restricted to administrators",
        ) from error
    except UserSelfManagementForbiddenError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrators cannot change their own account",
        ) from error
    except UserNotFoundError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from error


@router.patch(
    "/tickets/{ticket_id}/assignee",
    response_model=TicketRead,
)
async def reassign_ticket(
    ticket_id: UUID,
    data: TicketAssigneeUpdate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> TicketRead:
    use_case = ReassignTicket(
        ticket_repository=TicketRepository(session),
        user_repository=UserRepository(session),
    )

    try:
        ticket = await use_case.execute(
            ticket_id=ticket_id,
            data=data,
            current_user=current_user,
        )
        await session.commit()
        return ticket
    except TicketReassignmentForbiddenError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ticket reassignment is restricted to administrators",
        ) from error
    except TicketNotFoundError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        ) from error
    except UserNotFoundError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignee not found",
        ) from error
    except InvalidTicketAssigneeError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assignee must be an active support agent",
        ) from error
    except ClosedTicketReassignmentError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Closed tickets cannot be reassigned",
        ) from error
