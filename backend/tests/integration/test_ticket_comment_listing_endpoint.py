from uuid import UUID, uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient, Response

from app.comments.model import TicketComment
from app.main import app
from app.security.tokens import create_access_token
from app.tickets.model import TicketStatus
from app.users.model import UserRole
from tests.integration.helpers import (
    create_test_comment,
    create_test_ticket,
    create_test_user,
    delete_test_comment,
    delete_test_ticket,
    delete_test_user,
)


async def get_ticket_comments(
    *,
    ticket_id: UUID,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> Response:
    access_token = create_access_token(user_id)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(
            f"/api/v1/tickets/{ticket_id}/comments",
            params={"page": page, "page_size": page_size},
            headers={"Authorization": f"Bearer {access_token}"},
        )


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_gets_paginated_comments_for_own_ticket() -> None:
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
    comments: list[TicketComment] = []

    try:
        for number in range(3):
            comments.append(
                await create_test_comment(
                    ticket_id=ticket.id,
                    author_id=customer.id,
                    content=f"test-comment-{number}",
                )
            )

        expected_comments = sorted(
            comments,
            key=lambda comment: (comment.created_at, comment.id),
        )

        # Act
        first_response = await get_ticket_comments(
            ticket_id=ticket.id,
            user_id=customer.id,
            page=1,
            page_size=2,
        )
        second_response = await get_ticket_comments(
            ticket_id=ticket.id,
            user_id=customer.id,
            page=2,
            page_size=2,
        )

        # Assert
        assert first_response.status_code == status.HTTP_200_OK
        first_data = first_response.json()
        assert first_data["page"] == 1
        assert first_data["page_size"] == 2
        assert first_data["total"] == 3
        assert first_data["pages"] == 2
        assert [item["id"] for item in first_data["items"]] == [
            str(comment.id) for comment in expected_comments[:2]
        ]

        for item in first_data["items"]:
            assert set(item) == {
                "id",
                "ticket_id",
                "author_id",
                "content",
                "created_at",
            }

        assert second_response.status_code == status.HTTP_200_OK
        second_data = second_response.json()
        assert second_data["page"] == 2
        assert second_data["page_size"] == 2
        assert second_data["total"] == 3
        assert second_data["pages"] == 2
        assert [item["id"] for item in second_data["items"]] == [
            str(comment.id) for comment in expected_comments[2:]
        ]

    finally:
        for comment in comments:
            await delete_test_comment(comment.id)
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_assigned_agent_gets_ticket_comments() -> None:
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
        customer_id=customer.id,
        assignee_id=agent.id,
        status=TicketStatus.IN_PROGRESS,
    )
    comment = await create_test_comment(
        ticket_id=ticket.id,
        author_id=customer.id,
        content="customer-comment",
    )

    try:
        # Act
        response = await get_ticket_comments(
            ticket_id=ticket.id,
            user_id=agent.id,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["total"] == 1
        assert response_data["items"][0]["id"] == str(comment.id)

    finally:
        await delete_test_comment(comment.id)
        await delete_test_ticket(ticket.id)
        await delete_test_user(agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_admin_gets_comments_for_any_ticket() -> None:
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
        customer_id=customer.id,
    )
    comment = await create_test_comment(
        ticket_id=ticket.id,
        author_id=customer.id,
        content="customer-comment",
    )

    try:
        # Act
        response = await get_ticket_comments(
            ticket_id=ticket.id,
            user_id=admin.id,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["items"][0]["id"] == str(comment.id)

    finally:
        await delete_test_comment(comment.id)
        await delete_test_ticket(ticket.id)
        await delete_test_user(admin.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_gets_comments_for_closed_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )
    ticket = await create_test_ticket(
        title="test-title",
        customer_id=customer.id,
        status=TicketStatus.CLOSED,
    )
    comment = await create_test_comment(
        ticket_id=ticket.id,
        author_id=customer.id,
        content="existing-comment",
    )

    try:
        # Act
        response = await get_ticket_comments(
            ticket_id=ticket.id,
            user_id=customer.id,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["items"][0]["id"] == str(comment.id)

    finally:
        await delete_test_comment(comment.id)
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_cannot_view_another_customers_ticket_comments() -> None:
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
        customer_id=owner.id,
    )

    try:
        # Act
        response = await get_ticket_comments(
            ticket_id=ticket.id,
            user_id=other_customer.id,
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"detail": "Comment viewing is forbidden"}

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(other_customer.email)
        await delete_test_user(owner.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_unassigned_agent_cannot_view_ticket_comments() -> None:
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
        customer_id=customer.id,
    )

    try:
        # Act
        response = await get_ticket_comments(
            ticket_id=ticket.id,
            user_id=agent.id,
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"detail": "Comment viewing is forbidden"}

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_agent_cannot_view_another_agents_ticket_comments() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )
    assigned_agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )
    other_agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )
    ticket = await create_test_ticket(
        title="test-title",
        customer_id=customer.id,
        assignee_id=assigned_agent.id,
        status=TicketStatus.IN_PROGRESS,
    )

    try:
        # Act
        response = await get_ticket_comments(
            ticket_id=ticket.id,
            user_id=other_agent.id,
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"detail": "Comment viewing is forbidden"}

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(other_agent.email)
        await delete_test_user(assigned_agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_unknown_ticket_comments_cannot_be_viewed() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    try:
        # Act
        response = await get_ticket_comments(
            ticket_id=uuid4(),
            user_id=customer.id,
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Ticket not found"}

    finally:
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    ("page", "page_size"),
    [(0, 20), (-1, 20), (1, 0), (1, 101)],
)
async def test_comment_listing_rejects_invalid_pagination(
    page: int,
    page_size: int,
) -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )
    ticket = await create_test_ticket(
        title="test-title",
        customer_id=customer.id,
    )

    try:
        # Act
        response = await get_ticket_comments(
            ticket_id=ticket.id,
            user_id=customer.id,
            page=page,
            page_size=page_size,
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_comment_listing_requires_authentication() -> None:
    # Arrange
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Act
        response = await client.get(f"/api/v1/tickets/{uuid4()}/comments")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_blocked_user_cannot_view_ticket_comments() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        is_blocked=True,
    )
    ticket = await create_test_ticket(
        title="test-title",
        customer_id=customer.id,
    )

    try:
        # Act
        response = await get_ticket_comments(
            ticket_id=ticket.id,
            user_id=customer.id,
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"detail": "User account is blocked"}

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)
