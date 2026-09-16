from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.users.exceptions import (
    UserManagementForbiddenError,
    UserNotFoundError,
    UserSelfManagementForbiddenError,
)
from app.users.model import User, UserRole
from app.users.repository import UserRepository
from app.users.schemas import UserBlockedUpdate, UserRoleUpdate
from app.users.use_cases import ChangeUserBlockedStatus, ChangeUserRole


def make_user(
    *,
    user_id: UUID | None = None,
    role: UserRole = UserRole.CUSTOMER,
    is_blocked: bool = False,
) -> User:
    now = datetime.now(UTC)
    return User(
        id=user_id or uuid4(),
        email=f"user-{uuid4()}@example.com",
        hashed_password="hashed-password",
        role=role,
        is_blocked=is_blocked,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_admin_changes_user_role() -> None:
    admin = make_user(role=UserRole.ADMIN)
    target = make_user()
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_id.return_value = target
    repository.save.return_value = target

    result = await ChangeUserRole(repository).execute(
        user_id=target.id,
        data=UserRoleUpdate(role=UserRole.SUPPORT_AGENT),
        current_user=admin,
    )

    assert result.id == target.id
    assert result.role is UserRole.SUPPORT_AGENT
    repository.get_by_id.assert_awaited_once_with(target.id)
    repository.save.assert_awaited_once_with(target)


@pytest.mark.parametrize("role", [UserRole.CUSTOMER, UserRole.SUPPORT_AGENT])
@pytest.mark.asyncio
async def test_non_admin_cannot_change_user_role(role: UserRole) -> None:
    current_user = make_user(role=role)
    repository = AsyncMock(spec=UserRepository)

    with pytest.raises(UserManagementForbiddenError):
        await ChangeUserRole(repository).execute(
            user_id=uuid4(),
            data=UserRoleUpdate(role=UserRole.ADMIN),
            current_user=current_user,
        )

    repository.get_by_id.assert_not_awaited()
    repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_blocked_admin_cannot_change_user_role() -> None:
    admin = make_user(role=UserRole.ADMIN, is_blocked=True)
    repository = AsyncMock(spec=UserRepository)

    with pytest.raises(UserManagementForbiddenError):
        await ChangeUserRole(repository).execute(
            user_id=uuid4(),
            data=UserRoleUpdate(role=UserRole.SUPPORT_AGENT),
            current_user=admin,
        )

    repository.get_by_id.assert_not_awaited()
    repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_admin_cannot_change_own_role() -> None:
    admin = make_user(role=UserRole.ADMIN)
    repository = AsyncMock(spec=UserRepository)

    with pytest.raises(UserSelfManagementForbiddenError):
        await ChangeUserRole(repository).execute(
            user_id=admin.id,
            data=UserRoleUpdate(role=UserRole.CUSTOMER),
            current_user=admin,
        )

    repository.get_by_id.assert_not_awaited()
    repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_changing_unknown_user_role_fails() -> None:
    admin = make_user(role=UserRole.ADMIN)
    unknown_id = uuid4()
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await ChangeUserRole(repository).execute(
            user_id=unknown_id,
            data=UserRoleUpdate(role=UserRole.SUPPORT_AGENT),
            current_user=admin,
        )

    repository.get_by_id.assert_awaited_once_with(unknown_id)
    repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_admin_blocks_user() -> None:
    admin = make_user(role=UserRole.ADMIN)
    target = make_user()
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_id.return_value = target
    repository.save.return_value = target

    result = await ChangeUserBlockedStatus(repository).execute(
        user_id=target.id,
        data=UserBlockedUpdate(is_blocked=True),
        current_user=admin,
    )

    assert result.id == target.id
    assert result.is_blocked is True
    repository.get_by_id.assert_awaited_once_with(target.id)
    repository.save.assert_awaited_once_with(target)


@pytest.mark.parametrize("role", [UserRole.CUSTOMER, UserRole.SUPPORT_AGENT])
@pytest.mark.asyncio
async def test_non_admin_cannot_change_blocked_status(role: UserRole) -> None:
    current_user = make_user(role=role)
    repository = AsyncMock(spec=UserRepository)

    with pytest.raises(UserManagementForbiddenError):
        await ChangeUserBlockedStatus(repository).execute(
            user_id=uuid4(),
            data=UserBlockedUpdate(is_blocked=True),
            current_user=current_user,
        )

    repository.get_by_id.assert_not_awaited()
    repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_blocked_admin_cannot_change_blocked_status() -> None:
    admin = make_user(role=UserRole.ADMIN, is_blocked=True)
    repository = AsyncMock(spec=UserRepository)

    with pytest.raises(UserManagementForbiddenError):
        await ChangeUserBlockedStatus(repository).execute(
            user_id=uuid4(),
            data=UserBlockedUpdate(is_blocked=True),
            current_user=admin,
        )

    repository.get_by_id.assert_not_awaited()
    repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_admin_cannot_block_own_account() -> None:
    admin = make_user(role=UserRole.ADMIN)
    repository = AsyncMock(spec=UserRepository)

    with pytest.raises(UserSelfManagementForbiddenError):
        await ChangeUserBlockedStatus(repository).execute(
            user_id=admin.id,
            data=UserBlockedUpdate(is_blocked=True),
            current_user=admin,
        )

    repository.get_by_id.assert_not_awaited()
    repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_changing_unknown_user_blocked_status_fails() -> None:
    admin = make_user(role=UserRole.ADMIN)
    unknown_id = uuid4()
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await ChangeUserBlockedStatus(repository).execute(
            user_id=unknown_id,
            data=UserBlockedUpdate(is_blocked=True),
            current_user=admin,
        )

    repository.get_by_id.assert_awaited_once_with(unknown_id)
    repository.save.assert_not_awaited()
