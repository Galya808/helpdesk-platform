from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.tickets.model import TicketPriority, TicketStatus
from app.tickets.schemas import TicketCreate, TicketListQuery, TicketPage


def test_ticket_with_default_values_succeeds() -> None:
    # Arrange
    ticket = TicketCreate(
        title="test-title",
        description="test-description",
    )

    # Act + Assert
    assert ticket.title == "test-title"
    assert ticket.description == "test-description"
    assert ticket.priority is TicketPriority.MEDIUM


def test_ticket_with_defined_priority_succeeds() -> None:
    # Arrange
    ticket = TicketCreate(
        title="test-title", description="test-description", priority=TicketPriority.HIGH
    )

    # Act + Assert
    assert ticket.title == "test-title"
    assert ticket.description == "test-description"
    assert ticket.priority is TicketPriority.HIGH


def test_ticket_with_spaces_in_description_and_title_succeeds() -> None:
    # Arrange
    ticket = TicketCreate(
        title="  test-title  ",
        description="    test-description    ",
        priority=TicketPriority.HIGH,
    )

    # Act + Assert
    assert ticket.title == "test-title"
    assert ticket.description == "test-description"
    assert ticket.priority is TicketPriority.HIGH


def test_trimmed_short_title_raises_validation_error() -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        TicketCreate(
            title="      ab     ",
            description="test-description",
        )


def test_ticket_with_short_title_raises_validation_error() -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        TicketCreate(
            title="",
            description="test-description",
        )


def test_ticket_with_long_title_raises_validation_error() -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        TicketCreate(
            title="test-title" * 100,
            description="test-description",
        )


def test_ticket_with_short_description_raises_validation_error() -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        TicketCreate(
            title="test-title",
            description="invalid",
        )


def test_ticket_with_long_description_raises_validation_error() -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        TicketCreate(
            title="test-title",
            description="invalid-description" * 1000,
        )


def test_ticket_with_invalid_priority_raises_validation_error() -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        TicketCreate.model_validate(
            {
                "title": "test-title",
                "description": "test-description",
                "priority": "invalid-priority",
            }
        )


def test_ticket_with_defined_status_raises_validation_error() -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        TicketCreate.model_validate(
            {
                "title": "test-title",
                "description": "test-description",
                "status": "open",
            }
        )


def test_ticket_with_defined_customer_id_raises_validation_error() -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        TicketCreate.model_validate(
            {
                "title": "test-title",
                "description": "test-description",
                "customer_id": str(uuid4()),
            }
        )


def test_ticket_with_defined_assignee_id_raises_validation_error() -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        TicketCreate.model_validate(
            {
                "title": "test-title",
                "description": "test-description",
                "assignee_id": str(uuid4()),
            }
        )


def test_ticket_list_query_uses_defaults() -> None:
    # Arrange + Act
    ticket = TicketListQuery()

    # Assert
    assert ticket.page == 1
    assert ticket.page_size == 20
    assert ticket.status is None
    assert ticket.priority is None
    assert ticket.offset == 0


def test_ticket_list_query_calculates_offset() -> None:
    # Arrange + Act
    ticket = TicketListQuery(
        page=3,
        page_size=10,
    )

    # Assert
    assert ticket.offset == 20


@pytest.mark.parametrize(
    ("page", "page_size"),
    [
        (0, 20),
        (-1, 20),
        (1, 0),
        (1, 101),
    ],
)
def test_ticket_list_query_with_invalid_pagination(
    page: int,
    page_size: int,
) -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        TicketListQuery(
            page=page,
            page_size=page_size,
        )


def test_ticket_list_query_with_valid_filters() -> None:
    # Arrange + Act
    query = TicketListQuery(
        status=TicketStatus.OPEN,
        priority=TicketPriority.HIGH,
    )

    # Assert
    assert query.status is TicketStatus.OPEN
    assert query.priority is TicketPriority.HIGH


def test_ticket_list_query_with_invalid_status() -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        TicketListQuery.model_validate({"status": "unknown"})


def test_ticket_list_query_with_invalid_priority() -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        TicketListQuery.model_validate({"priority": "critical"})


def test_ticket_page_with_empty_items() -> None:
    # Arrange + Act
    page = TicketPage(
        items=[],
        page=1,
        page_size=20,
        total=0,
    )

    # Assert
    assert page.pages == 0
    assert page.model_dump()["pages"] == 0


def test_ticket_page_calculates_pages_with_rounding_up() -> None:
    # Arrange + Act
    page = TicketPage(
        items=[],
        page=1,
        page_size=20,
        total=41,
    )

    assert page.pages == 3
