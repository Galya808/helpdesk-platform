from uuid import UUID, uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.security.tokens import create_access_token
from app.tickets.model import TicketPriority, TicketStatus
from app.users.model import UserRole
from tests.integration.helpers import (
    create_test_ticket,
    create_test_user,
    delete_test_ticket,
    delete_test_user,
)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_lists_only_own_tickets() -> None:
    # Arrange
    first_customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    second_customer = await create_test_user(
        email=f"customer{uuid4()}@example.com",
        password="strong-password",
    )

    first_ticket = await create_test_ticket(
        title="first-test-title",
        description="first-test-description",
        customer_id=first_customer.id,
    )

    second_ticket = await create_test_ticket(
        title="second-test-title",
        description="second-test-description",
        customer_id=second_customer.id,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(first_customer.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                "/api/v1/tickets",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK

        item_ids = {UUID(item["id"]) for item in response_data["items"]}

        assert first_ticket.id in item_ids
        assert second_ticket.id not in item_ids

        assert response_data["page"] == 1
        assert response_data["page_size"] == 20
        assert response_data["total"] == 1
        assert response_data["pages"] == 1

    finally:
        await delete_test_ticket(first_ticket.id)
        await delete_test_ticket(second_ticket.id)
        await delete_test_user(first_customer.email)
        await delete_test_user(second_customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_support_agent_lists_assigned_and_unassigned_tickets() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    first_agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    second_agent = await create_test_user(
        email=f"agent-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.SUPPORT_AGENT,
    )

    first_assigned_ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=first_agent.id,
    )

    second_assigned_ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        assignee_id=second_agent.id,
    )

    unassigned_ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(first_agent.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                "/api/v1/tickets",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK

        ticket_ids = {UUID(item["id"]) for item in response_data["items"]}

        assert first_assigned_ticket.id in ticket_ids
        assert second_assigned_ticket.id not in ticket_ids
        assert unassigned_ticket.id in ticket_ids

        assert response_data["page"] == 1
        assert response_data["page_size"] == 20
        assert response_data["total"] == 2
        assert response_data["pages"] == 1

    finally:
        await delete_test_ticket(first_assigned_ticket.id)
        await delete_test_ticket(second_assigned_ticket.id)
        await delete_test_ticket(unassigned_ticket.id)
        await delete_test_user(first_agent.email)
        await delete_test_user(second_agent.email)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_admin_lists_all_tickets() -> None:
    # Arrange
    first_customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    second_customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    admin = await create_test_user(
        email=f"admin-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.ADMIN,
    )

    first_ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=first_customer.id,
    )

    second_ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=second_customer.id,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                "/api/v1/tickets",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK

        ticket_ids = {UUID(item["id"]) for item in response_data["items"]}

        assert first_ticket.id in ticket_ids
        assert second_ticket.id in ticket_ids

        assert response_data["page"] == 1
        assert response_data["page_size"] == 20
        assert response_data["total"] == 2
        assert response_data["pages"] == 1

    finally:
        await delete_test_ticket(first_ticket.id)
        await delete_test_ticket(second_ticket.id)
        await delete_test_user(first_customer.email)
        await delete_test_user(second_customer.email)
        await delete_test_user(admin.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_listing_filters_by_status_and_priority() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    first_ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        status=TicketStatus.OPEN,
        priority=TicketPriority.HIGH,
    )

    second_ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        status=TicketStatus.OPEN,
        priority=TicketPriority.LOW,
    )

    third_ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        status=TicketStatus.RESOLVED,
        priority=TicketPriority.HIGH,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(customer.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                "/api/v1/tickets?status=open&priority=high",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

            response_data = response.json()

        # Assert
        assert response.status_code == status.HTTP_200_OK

        ticket_ids = {UUID(item["id"]) for item in response_data["items"]}

        assert first_ticket.id in ticket_ids
        assert second_ticket.id not in ticket_ids
        assert third_ticket.id not in ticket_ids

        assert response_data["page"] == 1
        assert response_data["page_size"] == 20
        assert response_data["total"] == 1
        assert response_data["pages"] == 1

    finally:
        await delete_test_ticket(first_ticket.id)
        await delete_test_ticket(second_ticket.id)
        await delete_test_ticket(third_ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_listing_applies_pagination() -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
        role=UserRole.CUSTOMER,
    )

    first_ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        status=TicketStatus.OPEN,
        priority=TicketPriority.HIGH,
    )

    second_ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        status=TicketStatus.OPEN,
        priority=TicketPriority.LOW,
    )

    third_ticket = await create_test_ticket(
        title="test-title",
        description="test-description",
        customer_id=customer.id,
        status=TicketStatus.RESOLVED,
        priority=TicketPriority.HIGH,
    )

    transport = ASGITransport(app=app)
    access_token = create_access_token(customer.id)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            first_response = await client.get(
                "/api/v1/tickets?page=1&page_size=2",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

            second_response = await client.get(
                "/api/v1/tickets?page=2&page_size=2",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

            first_data = first_response.json()
            second_data = second_response.json()

        # Assert
        assert first_response.status_code == status.HTTP_200_OK
        assert second_response.status_code == status.HTTP_200_OK

        first_page_ids = {UUID(item["id"]) for item in first_data["items"]}
        second_page_ids = {UUID(item["id"]) for item in second_data["items"]}

        assert len(first_page_ids) == 2
        assert len(second_page_ids) == 1

        assert first_data["page"] == 1
        assert second_data["page"] == 2

        assert first_data["page_size"] == 2
        assert second_data["page_size"] == 2

        assert first_data["total"] == 3
        assert second_data["total"] == 3

        assert first_data["pages"] == 2
        assert second_data["pages"] == 2

        assert first_page_ids.isdisjoint(second_page_ids)
        assert first_page_ids | second_page_ids == {
            first_ticket.id,
            second_ticket.id,
            third_ticket.id,
        }

    finally:
        await delete_test_ticket(first_ticket.id)
        await delete_test_ticket(second_ticket.id)
        await delete_test_ticket(third_ticket.id)
        await delete_test_user(customer.email)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_listing_requires_authentication() -> None:
    # Arrange
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        # Act
        response = await client.get(
            "/api/v1/tickets",
        )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "query_string",
    [
        "page=0",
        "page=-1",
        "page_size=0",
        "page_size=101",
    ],
)
async def test_ticket_listing_rejects_invalid_pagination(query_string: str) -> None:
    # Arrange
    customer = await create_test_user(
        email=f"customer-{uuid4()}@example.com",
        password="strong-password",
    )

    access_token = create_access_token(customer.id)
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get(
                f"/api/v1/tickets?{query_string}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    finally:
        await delete_test_user(customer.email)
