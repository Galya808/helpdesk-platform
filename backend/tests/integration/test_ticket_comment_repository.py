from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.comments.model import TicketComment
from app.comments.repository import TicketCommentRepository
from app.database.session import async_session_factory
from tests.integration.helpers import (
    create_test_ticket,
    create_test_user,
    delete_test_ticket,
    delete_test_user,
)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_comment_repository_creates_comment() -> None:
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

    try:
        async with async_session_factory() as session:
            # Act
            repository = TicketCommentRepository(session)
            comment = await repository.create(
                ticket_id=ticket.id,
                author_id=customer.id,
                content="test-content",
            )

            statement = select(TicketComment).where(TicketComment.id == comment.id)
            result = await session.execute(statement)
            saved_comment = result.scalar_one_or_none()

            # Assert
            assert isinstance(comment.id, UUID)
            assert comment.ticket_id == ticket.id
            assert comment.author_id == customer.id
            assert comment.content == "test-content"
            assert comment.created_at is not None

            assert saved_comment is not None
            assert saved_comment.id == comment.id

            await session.rollback()

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_by_ticket_returns_only_requested_ticket_comments() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    first_ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )
    second_ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )

    try:
        async with async_session_factory() as session:
            # Act
            repository = TicketCommentRepository(session)
            first_comment = await repository.create(
                ticket_id=first_ticket.id,
                author_id=customer.id,
                content="test-content",
            )

            second_comment = await repository.create(
                ticket_id=first_ticket.id,
                author_id=customer.id,
                content="test-content",
            )

            third_comment = await repository.create(
                ticket_id=second_ticket.id,
                author_id=customer.id,
                content="test-content",
            )

            comments = await repository.list_by_ticket(
                ticket_id=first_ticket.id,
                offset=0,
                limit=100,
            )

            comment_ids = {comment.id for comment in comments}

            # Assert
            assert len(comments) == 2
            assert first_comment.id in comment_ids
            assert second_comment.id in comment_ids
            assert third_comment.id not in comment_ids
            assert all(comment.ticket_id == first_ticket.id for comment in comments)

            await session.rollback()

    finally:
        await delete_test_ticket(first_ticket.id)
        await delete_test_ticket(second_ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_by_ticket_orders_comments_and_applies_pagination() -> None:
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

    try:
        async with async_session_factory() as session:
            repository = TicketCommentRepository(session)

            first_comment = await repository.create(
                ticket_id=ticket.id,
                author_id=customer.id,
                content="first-comment",
            )
            second_comment = await repository.create(
                ticket_id=ticket.id,
                author_id=customer.id,
                content="second-comment",
            )
            third_comment = await repository.create(
                ticket_id=ticket.id,
                author_id=customer.id,
                content="third-comment",
            )

            expected_comments = sorted(
                [first_comment, second_comment, third_comment],
                key=lambda comment: (comment.created_at, comment.id),
            )

            # Act
            first_page = await repository.list_by_ticket(
                ticket_id=ticket.id,
                offset=0,
                limit=2,
            )
            second_page = await repository.list_by_ticket(
                ticket_id=ticket.id,
                offset=2,
                limit=2,
            )

            # Assert
            assert len(first_page) == 2
            assert len(second_page) == 1
            assert [comment.id for comment in first_page] == [
                comment.id for comment in expected_comments[:2]
            ]
            assert [comment.id for comment in second_page] == [
                comment.id for comment in expected_comments[2:]
            ]
            assert {comment.id for comment in first_page}.isdisjoint(
                {comment.id for comment in second_page}
            )

            await session.rollback()

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_count_by_ticket_counts_only_requested_ticket_comments() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    first_ticket = await create_test_ticket(
        title="first-title",
        description="first-description",
        customer_id=customer.id,
    )
    second_ticket = await create_test_ticket(
        title="second-title",
        description="second-description",
        customer_id=customer.id,
    )

    try:
        async with async_session_factory() as session:
            repository = TicketCommentRepository(session)

            await repository.create(
                ticket_id=first_ticket.id,
                author_id=customer.id,
                content="first-comment",
            )
            await repository.create(
                ticket_id=first_ticket.id,
                author_id=customer.id,
                content="second-comment",
            )
            await repository.create(
                ticket_id=second_ticket.id,
                author_id=customer.id,
                content="other-ticket-comment",
            )

            # Act
            count = await repository.count_by_ticket(first_ticket.id)

            # Assert
            assert count == 2

            await session.rollback()

    finally:
        await delete_test_ticket(first_ticket.id)
        await delete_test_ticket(second_ticket.id)
        await delete_test_user(customer.email)
