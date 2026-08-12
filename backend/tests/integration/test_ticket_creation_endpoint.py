from uuid import UUID, uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.database.session import async_session_factory
from app.main import app
from app.security.tokens import create_access_token
from app.tickets.model import Ticket, TicketPriority, TicketStatus
from app.users.model import UserRole
from tests.integration.helpers import (
    create_test_user,
    delete_test_ticket,
    delete_test_user,
)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_creates_ticket() -> None:
    # Arrange
    user_email = f"user-{uuid4()}@example.com"
    user_password = "strong-password"
    user = await create_test_user(
        email=user_email,
        password=user_password,
    )

    ticket_id: UUID | None = None
    title = "test-title"
    description = "test-description"
    priority = TicketPriority.HIGH

    transport = ASGITransport(app=app)

    access_token = create_access_token(user.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                "/api/v1/tickets",
                json={
                    "title": title,
                    "description": description,
                    "priority": priority,
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

        ticket_id = UUID(response_data["id"])

        assert response_data["title"] == title
        assert response_data["description"] == description
        assert response_data["priority"] == "high"
        assert response_data["status"] == "open"
        assert response_data["customer_id"] == str(user.id)
        assert response_data["assignee_id"] is None
        assert response_data["id"] is not None
        assert response_data["created_at"] is not None
        assert response_data["updated_at"] is not None

        async with async_session_factory() as session:
            statement = select(Ticket).where(Ticket.id == ticket_id)
            result = await session.execute(statement)
            saved_ticket = result.scalar_one_or_none()

            assert saved_ticket is not None
            assert saved_ticket.customer_id == user.id
            assert saved_ticket.priority is TicketPriority.HIGH
            assert saved_ticket.status is TicketStatus.OPEN
            assert saved_ticket.assignee_id is None

    finally:
        if ticket_id is not None:
            await delete_test_ticket(ticket_id)

        await delete_test_user(user_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_creates_ticket_with_default_priority() -> None:
    # Arrange
    user_email = f"user-{uuid4()}@example.com"
    user_password = "strong-password"

    user = await create_test_user(
        email=user_email,
        password=user_password,
    )

    title = "test-title"
    description = "test-description"
    ticket_id: UUID | None = None

    transport = ASGITransport(app=app)

    access_token = create_access_token(user.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                "/api/v1/tickets",
                json={
                    "title": title,
                    "description": description,
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

        ticket_id = UUID(response_data["id"])

        assert response_data["title"] == title
        assert response_data["description"] == description
        assert response_data["priority"] == "medium"
        assert response_data["status"] == "open"
        assert response_data["customer_id"] == str(user.id)
        assert response_data["assignee_id"] is None
        assert response_data["id"] is not None
        assert response_data["created_at"] is not None
        assert response_data["updated_at"] is not None

        async with async_session_factory() as session:
            statement = select(Ticket).where(Ticket.id == ticket_id)
            result = await session.execute(statement)
            saved_ticket = result.scalar_one_or_none()

            assert saved_ticket is not None
            assert saved_ticket.customer_id == user.id
            assert saved_ticket.priority is TicketPriority.MEDIUM
            assert saved_ticket.status is TicketStatus.OPEN
            assert saved_ticket.assignee_id is None

    finally:
        if ticket_id is not None:
            await delete_test_ticket(ticket_id)

        await delete_test_user(user_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_creation_requires_authentication() -> None:
    # Arrange
    transport = ASGITransport(app=app)

    title = "test-title"
    description = "test-description"

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        # Act
        response = await client.post(
            "/api/v1/tickets",
            json={
                "title": title,
                "description": description,
            },
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "detail": "Not authenticated",
        }
        assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_support_agent_cannot_create_ticket() -> None:
    # Arrange
    user_email = f"user-{uuid4()}@example.com"
    user_password = "strong-password"
    user = await create_test_user(
        email=user_email,
        password=user_password,
        role=UserRole.SUPPORT_AGENT,
    )

    title = "test-title"
    description = "test-description"

    transport = ASGITransport(app=app)

    access_token = create_access_token(user.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                "/api/v1/tickets",
                json={
                    "title": title,
                    "description": description,
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            "detail": "Only customers can create tickets",
        }

        async with async_session_factory() as session:
            statement = select(Ticket).where(Ticket.customer_id == user.id)
            result = await session.execute(statement)

            assert result.scalar_one_or_none() is None

    finally:
        await delete_test_user(user_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "payload",
    [
        {
            "title": "ab",
            "description": "valid description",
        },
        {
            "title": "valid title",
            "description": "ab",
        },
        {
            "title": "valid title",
            "description": "valid description",
            "priority": "critical",
        },
    ],
)
async def test_ticket_creation_rejects_invalid_data(
    payload: dict[str, object],
) -> None:
    # Arrange
    user_email = f"user-{uuid4()}@example.com"
    user_password = "strong-password"
    user = await create_test_user(
        email=user_email,
        password=user_password,
    )

    transport = ASGITransport(app=app)

    access_token = create_access_token(user.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                "/api/v1/tickets",
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        async with async_session_factory() as session:
            statement = select(Ticket).where(
                Ticket.customer_id == user.id,
            )
            result = await session.execute(statement)

            assert result.scalar_one_or_none() is None

    finally:
        await delete_test_user(user_email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_creation_rejects_protected_fields() -> None:
    # Arrange
    user_email = f"user-{uuid4()}@example.com"
    user_password = "strong-password"
    user = await create_test_user(
        email=user_email,
        password=user_password,
    )

    payload = {
        "title": "Valid title",
        "description": "Valid ticket description",
        "status": "closed",
        "customer_id": str(uuid4()),
        "assignee_id": str(uuid4()),
    }

    transport = ASGITransport(app=app)

    access_token = create_access_token(user.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                "/api/v1/tickets",
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        async with async_session_factory() as session:
            statement = select(Ticket).where(
                Ticket.customer_id == user.id,
            )
            result = await session.execute(statement)

            assert result.scalar_one_or_none() is None

    finally:
        await delete_test_user(user_email)
