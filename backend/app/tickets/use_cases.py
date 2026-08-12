from app.tickets.exceptions import TicketCreationForbiddenError
from app.tickets.model import Ticket
from app.tickets.repository import TicketRepository
from app.tickets.schemas import TicketCreate
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
