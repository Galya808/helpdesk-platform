from uuid import UUID, uuid4

import pytest

from app.database.session import async_session_factory
from app.users.model import UserRole
from app.users.repository import UserRepository


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_user_is_created() -> None:
    # Arrange
    email = f"user-{uuid4()}@example.com"

    async with async_session_factory() as session:
        repository = UserRepository(session)

        # Act
        created_user = await repository.create(
            email=email,
            hashed_password="hashed_password",
        )

        # Assert
        assert created_user.email == email
        assert isinstance(created_user.id, UUID)
        assert created_user.created_at is not None
        assert created_user.role is UserRole.CUSTOMER
        assert created_user.hashed_password == "hashed_password"

        # cancelling the session
        await session.rollback()


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_by_email() -> None:
    # Arrange
    email = f"user-{uuid4()}@example.com"

    async with async_session_factory() as session:
        repository = UserRepository(session)

        # Act
        await repository.create(
            email=email,
            hashed_password="hashed_password",
        )
        found_user = await repository.get_by_email(email)

        # Assert
        assert found_user is not None
        assert isinstance(found_user.id, UUID)
        assert found_user.email == email

        await session.rollback()


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_user_is_not_found() -> None:
    email = f"user-{uuid4()}@example.com"
    async with async_session_factory() as session:
        # Arrange
        repository = UserRepository(session)

        # Act
        found_user = await repository.get_by_email(email)

        # Assert
        assert found_user is None
