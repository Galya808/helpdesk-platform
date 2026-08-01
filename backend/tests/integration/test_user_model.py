from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.database.session import async_session_factory
from app.users.model import User, UserRole


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_database_assigns_user_defaults() -> None:
    email = f"user-{uuid4()}@example.com"

    async with async_session_factory() as session:
        user = User(
            email=email,
            hashed_password="hashed-password",
        )
        session.add(user)

        await session.flush()
        await session.refresh(user)

        assert isinstance(user.id, UUID)
        assert user.role is UserRole.CUSTOMER
        assert user.is_blocked is False
        assert user.created_at is not None
        assert user.updated_at is not None

        await session.rollback()


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_database_rejects_duplicate_user_email() -> None:
    email = f"duplicate-{uuid4()}@example.com"

    async with async_session_factory() as session:
        session.add(
            User(
                email=email,
                hashed_password="first-hashed-password",
            )
        )
        await session.flush()

        session.add(
            User(
                email=email,
                hashed_password="second-hashed-password",
            )
        )

        with pytest.raises(IntegrityError):
            await session.flush()

        await session.rollback()
