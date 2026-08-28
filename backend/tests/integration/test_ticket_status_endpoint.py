import asyncio
from uuid import uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.database.session import async_session_factory
from app.main import app
from app.security.tokens import create_access_token
from app.tickets.model import TicketStatus
from app.tickets.repository import TicketRepository
from app.users.model import UserRole
from tests.integration.helpers import (
    create_test_ticket,
    create_test_user,
    delete_test_ticket,
    delete_test_user,
)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_closes_own_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        status=TicketStatus.OPEN,
        customer_id=customer.id,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(customer.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/status",
                json={
                    "status": "closed",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(ticket.id)
        assert response_data["status"] == "closed"
        assert response_data["customer_id"] == str(ticket.customer_id)
        assert response_data["assignee_id"] is None
        assert response_data["title"] == ticket.title
        assert response_data["description"] == ticket.description
        assert response_data["priority"] == ticket.priority.value

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

            assert saved_ticket is not None
            assert saved_ticket.status is TicketStatus.CLOSED
            assert saved_ticket.customer_id == customer.id

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_reopens_own_resolved_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        status=TicketStatus.RESOLVED,
        customer_id=customer.id,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(customer.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/status",
                json={
                    "status": "in_progress",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(ticket.id)
        assert response_data["status"] == "in_progress"
        assert response_data["customer_id"] == str(ticket.customer_id)
        assert response_data["assignee_id"] is None
        assert response_data["title"] == ticket.title
        assert response_data["description"] == ticket.description
        assert response_data["priority"] == ticket.priority.value

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

            assert saved_ticket is not None
            assert saved_ticket.status is TicketStatus.IN_PROGRESS
            assert saved_ticket.customer_id == customer.id

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_assigned_agent_resolves_in_progress_ticket() -> None:
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
        status=TicketStatus.IN_PROGRESS,
        customer_id=customer.id,
        assignee_id=agent.id,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(agent.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/status",
                json={
                    "status": "resolved",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(ticket.id)
        assert response_data["status"] == "resolved"
        assert response_data["customer_id"] == str(ticket.customer_id)
        assert response_data["assignee_id"] == str(agent.id)
        assert response_data["title"] == ticket.title
        assert response_data["description"] == ticket.description
        assert response_data["priority"] == ticket.priority.value

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

            assert saved_ticket is not None
            assert saved_ticket.status is TicketStatus.RESOLVED
            assert saved_ticket.customer_id == customer.id
            assert saved_ticket.assignee_id == agent.id

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_admin_closes_resolved_ticket() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    admin = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.ADMIN,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        status=TicketStatus.RESOLVED,
        customer_id=customer.id,
        assignee_id=None,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/status",
                json={
                    "status": "closed",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(ticket.id)
        assert response_data["status"] == "closed"
        assert response_data["customer_id"] == str(ticket.customer_id)
        assert response_data["assignee_id"] is None
        assert response_data["title"] == ticket.title
        assert response_data["description"] == ticket.description
        assert response_data["priority"] == ticket.priority.value

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

            assert saved_ticket is not None
            assert saved_ticket.status is TicketStatus.CLOSED
            assert saved_ticket.customer_id == customer.id
            assert saved_ticket.assignee_id is None

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(admin.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_cannot_change_another_customers_ticket_status() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    owner = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        status=TicketStatus.OPEN,
        customer_id=owner.id,
        assignee_id=None,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(customer.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/status",
                json={
                    "status": "closed",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "Ticket status change is forbidden"

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

            assert saved_ticket is not None
            assert saved_ticket.status is TicketStatus.OPEN
            assert saved_ticket.customer_id == owner.id
            assert saved_ticket.assignee_id is None

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(owner.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_cannot_transition_open_ticket_to_resolved() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        status=TicketStatus.OPEN,
        customer_id=customer.id,
        assignee_id=None,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(customer.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/status",
                json={
                    "status": "resolved",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"] == "Invalid ticket status transition"

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

            assert saved_ticket is not None
            assert saved_ticket.status is TicketStatus.OPEN
            assert saved_ticket.customer_id == customer.id
            assert saved_ticket.assignee_id is None

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_status_change_for_unknown_ticket_returns_not_found() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    unknown_ticket_id = uuid4()

    transport = ASGITransport(app=app)
    access_token = create_access_token(customer.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.patch(
                f"/api/v1/tickets/{unknown_ticket_id}/status",
                json={
                    "status": "closed",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Ticket not found"

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(unknown_ticket_id)

            assert saved_ticket is None

    finally:
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_agent_cannot_change_ticket_assigned_to_another_agent() -> None:
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

    current_agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        status=TicketStatus.IN_PROGRESS,
        customer_id=customer.id,
        assignee_id=assigned_agent.id,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(current_agent.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/status",
                json={
                    "status": "resolved",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "Ticket status change is forbidden"

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

            assert saved_ticket is not None
            assert saved_ticket.status is TicketStatus.IN_PROGRESS
            assert saved_ticket.customer_id == customer.id
            assert saved_ticket.assignee_id == assigned_agent.id

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(assigned_agent.email)
        await delete_test_user(current_agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_closed_ticket_status_cannot_be_changed() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        status=TicketStatus.CLOSED,
        customer_id=customer.id,
        assignee_id=None,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(customer.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/status",
                json={
                    "status": "in_progress",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"] == "Invalid ticket status transition"

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

            assert saved_ticket is not None
            assert saved_ticket.status is TicketStatus.CLOSED
            assert saved_ticket.customer_id == customer.id
            assert saved_ticket.assignee_id is None

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_invalid_status_value_returns_validation_error() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        status=TicketStatus.OPEN,
        customer_id=customer.id,
        assignee_id=None,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(customer.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/status",
                json={
                    "status": "archived",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

            assert saved_ticket is not None
            assert saved_ticket.status is TicketStatus.OPEN
            assert saved_ticket.customer_id == customer.id
            assert saved_ticket.assignee_id is None

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_status_change_rejects_missing_token() -> None:
    # Arrange
    transport = ASGITransport(app=app)
    ticket_id = uuid4()

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        # Act
        response = await client.patch(
            f"/api/v1/tickets/{ticket_id}/status",
            json={
                "status": "closed",
            },
        )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"
    assert response.headers["WWW-Authenticate"] == "Bearer"

    async with async_session_factory() as session:
        repository = TicketRepository(session)
        saved_ticket = await repository.get_by_id(ticket_id)

        assert saved_ticket is None


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_blocked_customer_cannot_change_ticket_status() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        is_blocked=True,
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        status=TicketStatus.OPEN,
        customer_id=customer.id,
        assignee_id=None,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(customer.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.patch(
                f"/api/v1/tickets/{ticket.id}/status",
                json={
                    "status": "closed",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "User account is blocked"

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

            assert saved_ticket is not None
            assert saved_ticket.status is TicketStatus.OPEN
            assert saved_ticket.customer_id == customer.id
            assert saved_ticket.assignee_id is None

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_only_one_concurrent_status_transition_succeeds() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        status=TicketStatus.RESOLVED,
    )

    access_token = create_access_token(customer.id)
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            responses = await asyncio.gather(
                client.patch(
                    f"/api/v1/tickets/{ticket.id}/status",
                    json={
                        "status": "closed",
                    },
                    headers={
                        "Authorization": f"Bearer {access_token}",
                    },
                ),
                client.patch(
                    f"/api/v1/tickets/{ticket.id}/status",
                    json={
                        "status": "in_progress",
                    },
                    headers={
                        "Authorization": f"Bearer {access_token}",
                    },
                ),
            )

        # Assert
        assert sorted(response.status_code for response in responses) == [
            status.HTTP_200_OK,
            status.HTTP_409_CONFLICT,
        ]

        successful_response = next(
            response
            for response in responses
            if response.status_code == status.HTTP_200_OK
        )
        successful_data = successful_response.json()

        failed_response = next(
            response
            for response in responses
            if response.status_code == status.HTTP_409_CONFLICT
        )
        failed_data = failed_response.json()

        assert successful_data["status"] in {
            "closed",
            "in_progress",
        }
        assert successful_data["id"] == str(ticket.id)

        assert failed_data["detail"] == "Invalid ticket status transition"

        async with async_session_factory() as session:
            repository = TicketRepository(session)
            saved_ticket = await repository.get_by_id(ticket.id)

            assert saved_ticket is not None
            assert saved_ticket.status.value == successful_data["status"]
            assert saved_ticket.customer_id == customer.id
            assert saved_ticket.assignee_id is None

    finally:
        await delete_test_ticket(ticket.id)
        await delete_test_user(customer.email)
