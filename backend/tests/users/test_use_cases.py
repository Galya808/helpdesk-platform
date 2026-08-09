from unittest.mock import AsyncMock, patch

import pytest

from app.security.password import dummy_password_hash, hash_password, verify_password
from app.users.exceptions import (
    BlockedUserError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from app.users.model import User
from app.users.repository import UserRepository
from app.users.schemas import UserCreate, UserLogin
from app.users.use_cases import AuthenticateUser, RegisterUser


@pytest.mark.asyncio
async def test_user_is_registered_with_valid_credentials() -> None:
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
async def test_registration_fails_for_existing_email() -> None:
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


@pytest.mark.asyncio
async def test_user_is_authenticated_with_valid_credentials() -> None:
    # Arrange
    password = "strong-password"
    hashed_password = hash_password(password)

    user_data = UserLogin(
        email="USER@EXAMPLE.COM",
        password=password,
    )

    example_user = User(
        email="user@example.com",
        hashed_password=hashed_password,
    )

    repo = AsyncMock(spec=UserRepository)
    repo.get_by_email.return_value = example_user

    use_case = AuthenticateUser(repo)

    # Act
    current_user = await use_case.execute(user_data)

    # Assert
    assert current_user is example_user
    assert current_user.email == "user@example.com"

    repo.get_by_email.assert_awaited_once_with(user_data.email)
    repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_authentication_fails_for_unknown_email() -> None:
    # Arrange
    user_data = UserLogin(
        email="user@example.com",
        password="strong-password",
    )

    repo = AsyncMock(spec=UserRepository)
    repo.get_by_email.return_value = None

    use_case = AuthenticateUser(repo)

    # Act
    with patch(
        "app.users.use_cases.verify_password",
        return_value=False,
    ) as verify_password_mock:
        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(user_data)

        verify_password_mock.assert_called_once_with(
            user_data.password,
            dummy_password_hash,
        )

    # Assert
    repo.get_by_email.assert_awaited_once_with(str(user_data.email))
    repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_authentication_fails_for_unknown_password() -> None:
    # Arrange
    user_data = UserLogin(
        email="user@example.com",
        password="strong-password",
    )

    example_user = User(
        email="user@example.com",
        hashed_password=hash_password("incorrect-password"),
    )

    repo = AsyncMock(spec=UserRepository)
    repo.get_by_email.return_value = example_user

    use_case = AuthenticateUser(repo)

    # Act
    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(user_data)

    # Assert
    repo.get_by_email.assert_awaited_once_with(str(user_data.email))
    repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_authentication_fails_for_blocked_user() -> None:
    # Arrange
    password = "strong-password"
    hashed_password = hash_password(password)

    user_data = UserLogin(
        email="USER@EXAMPLE.COM",
        password=password,
    )

    example_user = User(
        email="user@example.com",
        hashed_password=hashed_password,
        is_blocked=True,
    )

    repo = AsyncMock(spec=UserRepository)
    repo.get_by_email.return_value = example_user

    use_case = AuthenticateUser(repo)

    # Act
    with pytest.raises(BlockedUserError):
        await use_case.execute(user_data)

    repo.get_by_email.assert_awaited_once_with(str(user_data.email))
    repo.create.assert_not_awaited()
