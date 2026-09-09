from uuid import UUID, uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.comments.model import TicketComment
from app.database.session import async_session_factory
from app.main import app
from app.security.tokens import create_access_token
from app.tickets.model import TicketStatus
from app.users.model import UserRole
from tests.integration.helpers import (
    create_test_ticket,
    create_test_user,
    delete_test_comment,
    delete_test_ticket,
    delete_test_user,
)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_adds_comment_to_own_ticket() -> None:
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

    comment_id: UUID | None = None

    access_token = create_access_token(customer.id)

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="https://test",
        ) as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/comments",
                json={
                    "content": "test-comment",
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

            response_data = response.json()

            # Assert
            assert response.status_code == status.HTTP_201_CREATED

            comment_id = UUID(response_data["id"])

            assert response_data["id"] is not None
            assert response_data["ticket_id"] == str(ticket.id)
            assert response_data["author_id"] == str(customer.id)
            assert response_data["content"] == "test-comment"
            assert response_data["created_at"] is not None

        async with async_session_factory() as session:
            statement = select(TicketComment).where(TicketComment.id == comment_id)
            result = await session.execute(statement)
            saved_comment = result.scalar_one_or_none()

            assert saved_comment is not None
            assert saved_comment.ticket_id == ticket.id
            assert saved_comment.author_id == customer.id
            assert saved_comment.content == "test-comment"

    finally:
        if comment_id is not None:
            await delete_test_comment(comment_id)

        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_assigned_agent_adds_comment_to_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=agent.id,
        status=TicketStatus.IN_PROGRESS,
    )

    comment_id: UUID | None = None

    access_token = create_access_token(agent.id)

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="https://test",
        ) as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/comments",
                json={
                    "content": "test-comment",
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

            response_data = response.json()

            # Assert
            assert response.status_code == status.HTTP_201_CREATED

            comment_id = UUID(response_data["id"])

            assert response_data["id"] is not None
            assert response_data["ticket_id"] == str(ticket.id)
            assert response_data["author_id"] == str(agent.id)
            assert response_data["content"] == "test-comment"
            assert response_data["created_at"] is not None

        async with async_session_factory() as session:
            statement = select(TicketComment).where(TicketComment.id == comment_id)
            result = await session.execute(statement)
            saved_comment = result.scalar_one_or_none()

            assert saved_comment is not None
            assert saved_comment.ticket_id == ticket.id
            assert saved_comment.author_id == agent.id
            assert saved_comment.content == "test-comment"

    finally:
        if comment_id is not None:
            await delete_test_comment(comment_id)

        await delete_test_ticket(ticket.id)
        await delete_test_user(agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_admin_adds_comment_to_any_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )
    admin = await create_test_user(
        email=f"admin-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.ADMIN,
    )
    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )
    access_token = create_access_token(admin.id)
    transport = ASGITransport(app=app)
    comment_id: UUID | None = None

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/comments",
                json={"content": "admin-comment"},
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        comment_id = UUID(response_data["id"])
        assert response_data["ticket_id"] == str(ticket.id)
        assert response_data["author_id"] == str(admin.id)
        assert response_data["content"] == "admin-comment"

    finally:
        if comment_id is not None:
            await delete_test_comment(comment_id)
        await delete_test_ticket(ticket.id)
        await delete_test_user(admin.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_cannot_comment_on_another_customers_ticket() -> None:
    # Arrange
    owner = await create_test_user(
        email=f"owner-{uuid4()}@example.com",
        password="strong-password",
    )
    other_customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )
    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=owner.id,
    )
    access_token = create_access_token(other_customer.id)
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/comments",
                json={"content": "forbidden-comment"},
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"detail": "Comment creation is forbidden"}

        async with async_session_factory() as session:
            statement = (
                select(func.count())
                .select_from(TicketComment)
                .where(TicketComment.ticket_id == ticket.id)
            )
            result = await session.execute(statement)
            assert result.scalar_one() == 0

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(other_customer.email)
        await delete_test_user(owner.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_unassigned_agent_cannot_comment_on_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )
    agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )
    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )
    access_token = create_access_token(agent.id)
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/comments",
                json={"content": "forbidden-comment"},
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"detail": "Comment creation is forbidden"}

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_comment_cannot_be_added_to_closed_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )
    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        status=TicketStatus.CLOSED,
    )
    access_token = create_access_token(customer.id)
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/comments",
                json={"content": "closed-ticket-comment"},
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {
            "detail": "Comments cannot be added to a closed ticket"
        }

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_comment_cannot_be_added_to_unknown_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )
    unknown_ticket_id = uuid4()
    access_token = create_access_token(customer.id)
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{unknown_ticket_id}/comments",
                json={"content": "test-comment"},
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Ticket not found"}

    finally:
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "content",
    ["", "   ", "a" * 5001],
    ids=["empty", "whitespace", "too-long"],
)
async def test_comment_creation_rejects_invalid_content(content: str) -> None:
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
    access_token = create_access_token(customer.id)
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/comments",
                json={"content": content},
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_comment_creation_requires_authentication() -> None:
    # Arrange
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Act
        response = await client.post(
            f"/api/v1/tickets/{uuid4()}/comments",
            json={"content": "test-comment"},
        )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_blocked_user_cannot_add_comment() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        is_blocked=True,
    )
    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )
    access_token = create_access_token(customer.id)
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/comments",
                json={"content": "test-comment"},
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"detail": "User account is blocked"}

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)
