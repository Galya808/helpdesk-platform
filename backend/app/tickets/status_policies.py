from app.tickets.model import Ticket, TicketStatus
from app.users.model import User


class CustomerTicketStatusPolicy:
    def has_access(
        self,
        ticket: Ticket,
        user: User,
    ) -> bool:
        return user.id == ticket.customer_id

    def allowed_statuses(
        self,
        ticket: Ticket,
        user: User,
    ) -> set[TicketStatus]:
        current_status = ticket.status

        if current_status is TicketStatus.OPEN:
            return {
                TicketStatus.CLOSED,
            }

        if current_status is TicketStatus.RESOLVED:
            return {
                TicketStatus.CLOSED,
                TicketStatus.IN_PROGRESS,
            }

        return set()


class SupportAgentTicketStatusPolicy:
    def has_access(
        self,
        ticket: Ticket,
        user: User,
    ) -> bool:
        return user.id == ticket.assignee_id

    def allowed_statuses(
        self,
        ticket: Ticket,
        user: User,
    ) -> set[TicketStatus]:
        current_status = ticket.status

        if current_status is TicketStatus.IN_PROGRESS:
            return {
                TicketStatus.RESOLVED,
            }

        if current_status is TicketStatus.RESOLVED:
            return {
                TicketStatus.CLOSED,
            }

        return set()
