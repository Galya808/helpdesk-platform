from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.tickets.model import Ticket, TicketPriority


class TicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        title: str,
        description: str,
        priority: TicketPriority,
        customer_id: UUID,
    ) -> Ticket:
        ticket = Ticket(
            title=title,
            description=description,
            priority=priority,
            customer_id=customer_id,
        )

        self.session.add(ticket)

        await self.session.flush()
        await self.session.refresh(ticket)

        return ticket
