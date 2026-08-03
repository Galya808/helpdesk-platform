from unittest.mock import AsyncMock

import pytest

from app.security.password import verify_password
from app.users.exceptions import EmailAlreadyRegisteredError
from app.users.model import User
from app.users.repository import UserRepository
from app.users.schemas import UserCreate
from app.users.use_cases import RegisterUser


@pytest.mark.asyncio
async def test_successful_registration() -> None:
    # Arrange
    user_data = UserCreate(
        email="USER@EXAMPLE.COM",
        password="strong-password",
    )

    example_user = User(
        email="user@example.com",
        hashed_password="hashed-strong-password",
    )

    repo = AsyncMock(spec=UserRepository)
    repo.get_by_email.return_value = None
    repo.create.return_value = example_user

    use_case = RegisterUser(repo)

    # Act
    created_user = await use_case.execute(user_data)

    # Assert
    assert created_user is example_user

    repo.get_by_email.assert_awaited_once_with(
        "user@example.com",
    )
    repo.create.assert_awaited_once()

    create_arguments = repo.create.await_args.kwargs

    assert create_arguments["email"] == user_data.email
    assert create_arguments["hashed_password"] != user_data.password
    assert verify_password(user_data.password, create_arguments["hashed_password"])


@pytest.mark.asyncio
async def test_register_existing_email() -> None:
    # Arrange
    user_data = UserCreate(
        email="user@example.com",
        password="strong-password",
    )
    existing_user = User(
        email="user@example.com",
        hashed_password="hashed-strong-password",
    )

    repo = AsyncMock(spec=UserRepository)
    repo.get_by_email.return_value = existing_user

    use_case = RegisterUser(repo)

    # Act + Assert
    with pytest.raises(
        EmailAlreadyRegisteredError,
    ):
        await use_case.execute(user_data)

    repo.get_by_email.assert_awaited_once_with(str(user_data.email))
    repo.create.assert_not_awaited()
