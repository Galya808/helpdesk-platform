from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.security.exceptions import InvalidAccessTokenError
from app.users.model import User
from app.users.repository import UserRepository


@pytest.mark.asyncio
async def test_get_current_user_returns_authenticated_user() -> None:
    # Arrange
    user_id = uuid4()

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="example-token",
    )

    session = AsyncMock(spec=AsyncSession)

    expected_user = User(
        id=user_id,
        email="user@example.com",
        hashed_password="hashed-password",
        is_blocked=False,
    )

    repository = AsyncMock(spec=UserRepository)
    repository.get_by_id.return_value = expected_user

    with (
        patch(
            "app.api.dependencies.decode_access_token",
            return_value=user_id,
        ) as decode_token_mock,
        patch(
            "app.api.dependencies.UserRepository",
            return_value=repository,
        ) as repository_class_mock,
    ):
        # Act
        current_user = await get_current_user(
            credentials=credentials,
            session=session,
        )

    # Assert
    assert current_user is expected_user

    decode_token_mock.assert_called_once_with(
        credentials.credentials,
    )

    repository_class_mock.assert_called_once_with(session)
    repository.get_by_id.assert_awaited_once_with(user_id)


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_credentials() -> None:
    # Arrange
    session = AsyncMock(spec=AsyncSession)

    with (
        patch(
            "app.api.dependencies.UserRepository",
        ) as repository_class_mock,
        pytest.raises(HTTPException) as exception_info,
    ):
        # Act + Assert
        await get_current_user(
            credentials=None,
            session=session,
        )

    assert exception_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exception_info.value.detail == "Not authenticated"
    assert exception_info.value.headers == {
        "WWW-Authenticate": "Bearer",
    }

    repository_class_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_token() -> None:
    # Arrange
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="example-token",
    )

    session = AsyncMock(spec=AsyncSession)

    with (
        patch(
            "app.api.dependencies.decode_access_token",
            side_effect=InvalidAccessTokenError,
        ) as decode_token_mock,
        patch(
            "app.api.dependencies.UserRepository",
        ) as repository_class_mock,
        pytest.raises(HTTPException) as exception_info,
    ):
        # Act + Assert
        await get_current_user(
            credentials=credentials,
            session=session,
        )

    assert exception_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exception_info.value.detail == "Invalid or expired access token"
    assert exception_info.value.headers == {"WWW-Authenticate": "Bearer"}

    decode_token_mock.assert_called_once_with(
        credentials.credentials,
    )

    repository_class_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_user() -> None:
    # Arrange
    user_id = uuid4()

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="example-token",
    )

    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_id.return_value = None

    with (
        patch(
            "app.api.dependencies.decode_access_token",
            return_value=user_id,
        ) as decode_token_mock,
        patch(
            "app.api.dependencies.UserRepository",
            return_value=repository,
        ) as repository_class_mock,
        pytest.raises(HTTPException) as exception_info,
    ):
        # Act + Assert
        await get_current_user(
            credentials=credentials,
            session=session,
        )

    assert exception_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exception_info.value.detail == "Invalid or expired access token"
    assert exception_info.value.headers == {
        "WWW-Authenticate": "Bearer",
    }

    decode_token_mock.assert_called_once_with(
        credentials.credentials,
    )
    repository_class_mock.assert_called_once_with(session)
    repository.get_by_id.assert_awaited_once_with(user_id)


@pytest.mark.asyncio
async def test_get_current_user_rejects_blocked_user() -> None:
    user_id = uuid4()

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="example-token",
    )

    expected_user = User(
        id=user_id,
        email="user@example.com",
        hashed_password="hashed_password",
        is_blocked=True,
    )

    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_id.return_value = expected_user

    with (
        patch(
            "app.api.dependencies.decode_access_token",
            return_value=user_id,
        ) as decode_token_mock,
        patch(
            "app.api.dependencies.UserRepository", return_value=repository
        ) as repository_class_mock,
        pytest.raises(HTTPException) as exception_info,
    ):
        await get_current_user(
            credentials=credentials,
            session=session,
        )

    assert exception_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exception_info.value.detail == "User account is blocked"

    decode_token_mock.assert_called_once_with(
        credentials.credentials,
    )
    repository_class_mock.assert_called_once_with(session)
    repository.get_by_id.assert_awaited_once_with(user_id)
