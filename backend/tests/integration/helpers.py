from uuid import UUID

from sqlalchemy import delete

from app.database.session import async_session_factory
from app.security.password import hash_password
from app.tickets.model import Ticket, TicketPriority, TicketStatus
from app.users.model import User, UserRole


async def create_test_user(
    email: str,
    password: str,
    role: UserRole = UserRole.CUSTOMER,
    is_blocked: bool = False,
) -> User:
    async with async_session_factory() as session, session.begin():
        user = User(
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_blocked=is_blocked,
        )

        session.add(user)

        await session.flush()
        await session.refresh(user)

        return user


async def delete_test_user(
    email: str,
) -> None:
    async with async_session_factory() as session, session.begin():
        await session.execute(delete(User).where(User.email == email))


async def create_test_ticket(
    customer_id: UUID,
    title: str,
    description: str = "test_description",
    status: TicketStatus = TicketStatus.OPEN,
    priority: TicketPriority = TicketPriority.MEDIUM,
    assignee_id: UUID | None = None,
) -> Ticket:
    async with async_session_factory() as session, session.begin():
        ticket = Ticket(
            customer_id=customer_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
        )

        session.add(ticket)

        await session.flush()
        await session.refresh(ticket)

        return ticket


async def delete_test_ticket(
    ticket_id: UUID,
) -> None:
    async with async_session_factory() as session, session.begin():
        await session.execute(delete(Ticket).where(Ticket.id == ticket_id))
