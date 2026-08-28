from uuid import UUID

from app.tickets.exceptions import (
    InvalidTicketStatusTransitionError,
    TicketAlreadyAssignedError,
    TicketAssignmentForbiddenError,
    TicketCreationForbiddenError,
    TicketNotAssignableError,
    TicketNotFoundError,
    TicketStatusChangeForbiddenError,
)
from app.tickets.model import Ticket, TicketStatus
from app.tickets.repository import TicketRepository
from app.tickets.schemas import (
    TicketCreate,
    TicketListQuery,
    TicketPage,
    TicketRead,
    TicketStatusUpdate,
)
from app.tickets.status_policies import create_ticket_status_policy
from app.users.model import User, UserRole


class CreateTicket:
    def __init__(self, repository: TicketRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        data: TicketCreate,
        current_user: User,
    ) -> Ticket:
        if current_user.role is not UserRole.CUSTOMER:
            raise TicketCreationForbiddenError

        created_ticket = await self.repository.create(
            title=data.title,
            description=data.description,
            priority=data.priority,
            customer_id=current_user.id,
        )

        return created_ticket


class ListTickets:
    def __init__(self, repository: TicketRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        query: TicketListQuery,
        current_user: User,
    ) -> TicketPage:
        if current_user.role is UserRole.CUSTOMER:
            tickets = await self.repository.list(
                customer_id=current_user.id,
                assignee_id=None,
                include_unassigned=False,
                status=query.status,
                priority=query.priority,
                offset=query.offset,
                limit=query.page_size,
            )

            ticket_count = await self.repository.count(
                customer_id=current_user.id,
                assignee_id=None,
                include_unassigned=False,
                status=query.status,
                priority=query.priority,
            )

        elif current_user.role is UserRole.SUPPORT_AGENT:
            tickets = await self.repository.list(
                customer_id=None,
                assignee_id=current_user.id,
                include_unassigned=True,
                status=query.status,
                priority=query.priority,
                offset=query.offset,
                limit=query.page_size,
            )

            ticket_count = await self.repository.count(
                customer_id=None,
                assignee_id=current_user.id,
                include_unassigned=True,
                status=query.status,
                priority=query.priority,
            )

        elif current_user.role is UserRole.ADMIN:
            tickets = await self.repository.list(
                customer_id=None,
                assignee_id=None,
                include_unassigned=False,
                status=query.status,
                priority=query.priority,
                offset=query.offset,
                limit=query.page_size,
            )

            ticket_count = await self.repository.count(
                customer_id=None,
                assignee_id=None,
                include_unassigned=False,
                status=query.status,
                priority=query.priority,
            )

        ticket_items = [TicketRead.model_validate(ticket) for ticket in tickets]

        return TicketPage(
            items=ticket_items,
            page=query.page,
            page_size=query.page_size,
            total=ticket_count,
        )


class GetTicket:
    def __init__(self, repository: TicketRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        ticket_id: UUID,
        current_user: User,
    ) -> TicketRead:
        ticket = await self.repository.get_by_id(ticket_id)

        if ticket is None:
            raise TicketNotFoundError

        has_access = False

        if current_user.role is UserRole.CUSTOMER:
            has_access = ticket.customer_id == current_user.id

        elif current_user.role is UserRole.SUPPORT_AGENT:
            has_access = (
                ticket.assignee_id is None or ticket.assignee_id == current_user.id
            )

        elif current_user.role is UserRole.ADMIN:
            has_access = True

        if not has_access:
            raise TicketNotFoundError

        return TicketRead.model_validate(ticket)


class AssignTicket:
    def __init__(self, repository: TicketRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        ticket_id: UUID,
        current_user: User,
    ) -> TicketRead:
        if current_user.role is not UserRole.SUPPORT_AGENT or current_user.is_blocked:
            raise TicketAssignmentForbiddenError

        ticket = await self.repository.get_by_id_for_update(ticket_id)

        if ticket is None:
            raise TicketNotFoundError

        if ticket.assignee_id is not None:
            raise TicketAlreadyAssignedError

        if ticket.status is not TicketStatus.OPEN:
            raise TicketNotAssignableError

        ticket.assignee_id = current_user.id
        ticket.status = TicketStatus.IN_PROGRESS

        updated_ticket = await self.repository.save(ticket)

        return TicketRead.model_validate(updated_ticket)


class ChangeTicketStatus:
    def __init__(self, repository: TicketRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        ticket_id: UUID,
        data: TicketStatusUpdate,
        current_user: User,
    ) -> TicketRead:
        if current_user.is_blocked:
            raise TicketStatusChangeForbiddenError

        ticket = await self.repository.get_by_id_for_update(ticket_id)

        if ticket is None:
            raise TicketNotFoundError

        policy = create_ticket_status_policy(current_user.role)

        has_access = policy.has_access(ticket, current_user)

        if not has_access:
            raise TicketStatusChangeForbiddenError

        allowed_statuses = policy.allowed_statuses(
            ticket=ticket,
            user=current_user,
        )

        if data.status not in allowed_statuses:
            raise InvalidTicketStatusTransitionError

        ticket.status = data.status

        updated_ticket = await self.repository.save(ticket)

        return TicketRead.model_validate(updated_ticket)
