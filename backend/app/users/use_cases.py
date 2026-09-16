from uuid import UUID

from app.security.password import dummy_password_hash, hash_password, verify_password
from app.users.exceptions import (
    BlockedUserError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    UserManagementForbiddenError,
    UserNotFoundError,
    UserSelfManagementForbiddenError,
)
from app.users.model import User, UserRole
from app.users.repository import UserRepository
from app.users.schemas import (
    UserBlockedUpdate,
    UserCreate,
    UserListQuery,
    UserLogin,
    UserPage,
    UserRead,
    UserRoleUpdate,
)


# This class provides one scenario of the application: register the user
class RegisterUser:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def execute(self, data: UserCreate) -> User:
        email = str(data.email)

        existing_user = await self.repository.get_by_email(email)

        if existing_user is not None:
            raise EmailAlreadyRegisteredError

        hashed_password = hash_password(data.password)

        created_user = await self.repository.create(
            email=email,
            hashed_password=hashed_password,
        )

        return created_user


class AuthenticateUser:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def execute(self, data: UserLogin) -> User:
        email = str(data.email)

        existing_user = await self.repository.get_by_email(email)

        if existing_user is None:
            verify_password(
                data.password,
                dummy_password_hash,
            )

            raise InvalidCredentialsError

        if not verify_password(data.password, existing_user.hashed_password):
            raise InvalidCredentialsError

        if existing_user.is_blocked:
            raise BlockedUserError

        return existing_user


class ListUsers:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        query: UserListQuery,
        current_user: User,
    ) -> UserPage:
        if current_user.role is not UserRole.ADMIN or current_user.is_blocked:
            raise UserManagementForbiddenError

        users = await self.repository.list(
            offset=query.offset,
            limit=query.page_size,
        )

        user_count = await self.repository.count()

        items = [UserRead.model_validate(user) for user in users]

        return UserPage(
            items=items,
            page=query.page,
            page_size=query.page_size,
            total=user_count,
        )


class ChangeUserRole:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        *,
        user_id: UUID,
        data: UserRoleUpdate,
        current_user: User,
    ) -> UserRead:
        if current_user.role is not UserRole.ADMIN or current_user.is_blocked:
            raise UserManagementForbiddenError

        if user_id == current_user.id:
            raise UserSelfManagementForbiddenError

        user = await self.repository.get_by_id(user_id)

        if user is None:
            raise UserNotFoundError

        user.role = data.role
        saved_user = await self.repository.save(user)

        return UserRead.model_validate(saved_user)


class ChangeUserBlockedStatus:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        *,
        user_id: UUID,
        data: UserBlockedUpdate,
        current_user: User,
    ) -> UserRead:
        if current_user.role is not UserRole.ADMIN or current_user.is_blocked:
            raise UserManagementForbiddenError

        if user_id == current_user.id:
            raise UserSelfManagementForbiddenError

        user = await self.repository.get_by_id(user_id)

        if user is None:
            raise UserNotFoundError

        user.is_blocked = data.is_blocked
        saved_user = await self.repository.save(user)

        return UserRead.model_validate(saved_user)
