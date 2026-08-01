import pytest
from pydantic import ValidationError

from app.users.schemas import UserCreate


def test_user_is_created_correctly():
    # Arrange + Act
    user = UserCreate(
        email="user@example.com",
        password="strong-password",
    )

    # Assert
    assert str(user.email) == "user@example.com"
    assert user.password == "strong-password"


def test_email_is_normalized_correctly():
    # Arrange + Act
    user = UserCreate(
        email="  USER@EXAMPLE.COM  ",
        password="strong-password",
    )

    # Assert
    assert str(user.email) == "user@example.com"


def test_incorrect_user_email_raises_validation_error():
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        UserCreate(
            email="email",
            password="strong-password",
        )


def test_password_less_than_12_symbols_raises_validation_error():
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        UserCreate(
            email="user@example.com",
            password="password",
        )
