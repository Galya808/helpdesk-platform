from sqlalchemy import delete

from app.database.session import async_session_factory
from app.security.password import hash_password
from app.users.model import User, UserRole


async def create_test_user(
    email: str,
    password: str,
    role: UserRole = UserRole.CUSTOMER,
    is_blocked: bool = False,
) -> User:
    async with async_session_factory() as session, session.begin():
        user = User(
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_blocked=is_blocked,
        )

        session.add(user)

        await session.flush()
        await session.refresh(user)

        return user


async def delete_test_user(
    email: str,
) -> None:
    async with async_session_factory() as session, session.begin():
        await session.execute(delete(User).where(User.email == email))
