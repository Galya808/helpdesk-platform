from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.comments.model import TicketComment


class TicketCommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        ticket_id: UUID,
        author_id: UUID,
        content: str,
    ) -> TicketComment:
        comment = TicketComment(
            ticket_id=ticket_id,
            author_id=author_id,
            content=content,
        )

        self.session.add(comment)

        await self.session.flush()
        await self.session.refresh(comment)

        return comment

    async def list_by_ticket(
        self,
        *,
        ticket_id: UUID,
        offset: int,
        limit: int,
    ) -> list[TicketComment]:
        statement = select(TicketComment).where(TicketComment.ticket_id == ticket_id)

        statement = (
            statement.order_by(
                TicketComment.created_at.asc(),
                TicketComment.id.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def count_by_ticket(
        self,
        ticket_id: UUID,
    ) -> int:
        statement = select(func.count()).select_from(TicketComment)

        statement = statement.where(TicketComment.ticket_id == ticket_id)

        result = await self.session.execute(statement)

        return result.scalar_one()
