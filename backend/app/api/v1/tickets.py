from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.tickets.exceptions import (
    InvalidTicketStatusTransitionError,
    TicketAlreadyAssignedError,
    TicketAssignmentForbiddenError,
    TicketCreationForbiddenError,
    TicketNotAssignableError,
    TicketNotFoundError,
    TicketStatusChangeForbiddenError,
)
from app.tickets.model import Ticket
from app.tickets.repository import TicketRepository
from app.tickets.schemas import (
    TicketCreate,
    TicketListQuery,
    TicketPage,
    TicketRead,
    TicketStatusUpdate,
)
from app.tickets.use_cases import (
    AssignTicket,
    ChangeTicketStatus,
    CreateTicket,
    GetTicket,
    ListTickets,
)

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
)

TicketQuery = Annotated[
    TicketListQuery,
    Depends(),
]


@router.get(
    "",
    response_model=TicketPage,
)
async def list_tickets(
    query: TicketQuery,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> TicketPage:
    repository = TicketRepository(session)
    use_case = ListTickets(repository)
    result = await use_case.execute(
        query=query,
        current_user=current_user,
    )

    return result


@router.get(
    "/{ticket_id}",
    response_model=TicketRead,
)
async def get_ticket(
    ticket_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> TicketRead:
    repository = TicketRepository(session)
    use_case = GetTicket(repository)

    try:
        ticket = await use_case.execute(
            ticket_id=ticket_id,
            current_user=current_user,
        )

        return ticket

    except TicketNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        ) from error


@router.post(
    "",
    response_model=TicketRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket(
    ticket_data: TicketCreate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Ticket:
    repository = TicketRepository(session)
    use_case = CreateTicket(repository)

    try:
        created_ticket = await use_case.execute(
            data=ticket_data,
            current_user=current_user,
        )

        await session.commit()

        return created_ticket
    except TicketCreationForbiddenError as error:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create tickets",
        ) from error


@router.post(
    "/{ticket_id}/assign", response_model=TicketRead, status_code=status.HTTP_200_OK
)
async def assign_ticket(
    ticket_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> TicketRead:
    try:
        repository = TicketRepository(session)
        use_case = AssignTicket(repository)

        ticket = await use_case.execute(
            ticket_id=ticket_id,
            current_user=current_user,
        )

        await session.commit()

        return ticket

    except TicketAssignmentForbiddenError as error:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only active support agents can assign tickets",
        ) from error

    except TicketNotFoundError as error:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        ) from error

    except TicketAlreadyAssignedError as error:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ticket is already assigned",
        ) from error

    except TicketNotAssignableError as error:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ticket cannot be assigned in its current state",
        ) from error


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketRead,
    status_code=status.HTTP_200_OK,
)
async def update_ticket_status(
    ticket_id: UUID,
    data: TicketStatusUpdate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> TicketRead:
    repository = TicketRepository(session)
    use_case = ChangeTicketStatus(repository)

    try:
        updated_ticket = await use_case.execute(
            ticket_id=ticket_id,
            data=data,
            current_user=current_user,
        )

        await session.commit()

        return updated_ticket

    except TicketNotFoundError as error:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        ) from error

    except TicketStatusChangeForbiddenError as error:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ticket status change is forbidden",
        ) from error

    except InvalidTicketStatusTransitionError as error:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid ticket status transition",
        ) from error
