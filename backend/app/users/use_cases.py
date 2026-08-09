from app.security.password import dummy_password_hash, hash_password, verify_password
from app.users.exceptions import (
    BlockedUserError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from app.users.model import User
from app.users.repository import UserRepository
from app.users.schemas import UserCreate, UserLogin


# This class provides one scenario of the application: register the user
class RegisterUser:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def execute(self, data: UserCreate) -> User:
        email = str(data.email)

        existing_user = await self.repo.get_by_email(email)

        if existing_user is not None:
            raise EmailAlreadyRegisteredError

        hashed_password = hash_password(data.password)

        created_user = await self.repo.create(
            email=email,
            hashed_password=hashed_password,
        )

        return created_user


class AuthenticateUser:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def execute(self, data: UserLogin) -> User:
        email = str(data.email)

        existing_user = await self.repo.get_by_email(email)

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
