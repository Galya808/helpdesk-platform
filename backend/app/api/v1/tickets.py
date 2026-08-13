from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.tickets.exceptions import TicketCreationForbiddenError
from app.tickets.model import Ticket
from app.tickets.repository import TicketRepository
from app.tickets.schemas import TicketCreate, TicketListQuery, TicketPage, TicketRead
from app.tickets.use_cases import CreateTicket, ListTickets

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
