from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.model import User


class UserRepository:
    # Dependency Injection. Repository receives the ready session
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        email: str,
        hashed_password: str,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
        )

        self.session.add(user)

        # flush sends INSERT into PostgreSQL, but does not finish the transaction
        await self.session.flush()
        # refresh loads data into the user
        await self.session.refresh(user)

        return user
