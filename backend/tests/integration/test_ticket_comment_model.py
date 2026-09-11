from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.comments.model import TicketComment
from app.database.session import async_session_factory
from tests.integration.helpers import (
    create_test_ticket,
    create_test_user,
    delete_test_ticket,
    delete_test_user,
)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_comment_is_created() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )

    comment = TicketComment(
        ticket_id=ticket.id,
        author_id=customer.id,
        content="test-comment",
    )

    try:
        async with async_session_factory() as session:
            # Act
            session.add(comment)

            await session.flush()
            await session.refresh(comment)

            # Assert
            assert isinstance(comment.id, UUID)
            assert comment.ticket_id == ticket.id
            assert comment.author_id == customer.id
            assert comment.content == "test-comment"
            assert comment.created_at is not None

            await session.rollback()

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_comment_rejects_unknown_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    ticket_id = uuid4()

    comment = TicketComment(
        ticket_id=ticket_id,
        author_id=customer.id,
        content="test-comment",
    )

    try:
        async with async_session_factory() as session:
            # Act
            session.add(comment)

            # Assert
            with pytest.raises(IntegrityError):
                await session.flush()

            await session.rollback()

    finally:
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_comment_rejects_unknown_author() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )

    comment = TicketComment(
        ticket_id=ticket.id,
        author_id=uuid4(),
        content="test-comment",
    )

    try:
        async with async_session_factory() as session:
            # Act
            session.add(comment)

            # Assert
            with pytest.raises(IntegrityError):
                await session.flush()

            await session.rollback()

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_deletion_cascades_to_comments() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )

    comment = TicketComment(
        ticket_id=ticket.id,
        author_id=customer.id,
        content="test-comment",
    )

    try:
        async with async_session_factory() as session, session.begin():
            # Act
            session.add(comment)

            await session.flush()
            await session.refresh(comment)

            comment_id = comment.id

        await delete_test_ticket(ticket.id)

        async with async_session_factory() as session:
            statement = select(TicketComment).where(TicketComment.id == comment_id)
            result = await session.execute(statement)

            assert result.scalar_one_or_none() is None

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)
