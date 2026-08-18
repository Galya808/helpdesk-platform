from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.tickets.model import Ticket, TicketPriority, TicketStatus


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

    async def list(
        self,
        *,
        customer_id: UUID | None,
        assignee_id: UUID | None,
        include_unassigned: bool,
        status: TicketStatus | None,
        priority: TicketPriority | None,
        offset: int,
        limit: int,
    ) -> list[Ticket]:
        statement = select(Ticket)

        if customer_id is not None:
            statement = statement.where(Ticket.customer_id == customer_id)

        if assignee_id is not None:
            if include_unassigned:
                statement = statement.where(
                    or_(
                        Ticket.assignee_id == assignee_id,
                        Ticket.assignee_id.is_(None),
                    )
                )
            else:
                statement = statement.where(Ticket.assignee_id == assignee_id)

        if status is not None:
            statement = statement.where(Ticket.status == status)

        if priority is not None:
            statement = statement.where(Ticket.priority == priority)

        statement = (
            statement.order_by(
                Ticket.created_at.desc(),
                Ticket.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def count(
        self,
        *,
        customer_id: UUID | None,
        assignee_id: UUID | None,
        include_unassigned: bool,
        status: TicketStatus | None,
        priority: TicketPriority | None,
    ) -> int:
        statement = select(func.count()).select_from(Ticket)

        if customer_id is not None:
            statement = statement.where(Ticket.customer_id == customer_id)

        if assignee_id is not None:
            if include_unassigned:
                statement = statement.where(
                    or_(
                        Ticket.assignee_id == assignee_id,
                        Ticket.assignee_id.is_(None),
                    )
                )
            else:
                statement = statement.where(Ticket.assignee_id == assignee_id)

        if status is not None:
            statement = statement.where(Ticket.status == status)

        if priority is not None:
            statement = statement.where(Ticket.priority == priority)

        result = await self.session.execute(statement)

        return result.scalar_one()

    async def get_by_id(
        self,
        ticket_id: UUID,
    ) -> Ticket | None:
        statement = select(Ticket).where(Ticket.id == ticket_id)

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_id_for_update(
        self,
        ticket_id: UUID,
    ) -> Ticket | None:
        statement = select(Ticket).where(Ticket.id == ticket_id).with_for_update()

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()
