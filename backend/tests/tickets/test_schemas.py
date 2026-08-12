from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.tickets.model import TicketPriority
from app.tickets.schemas import TicketCreate


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
