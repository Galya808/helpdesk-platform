from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import DatabaseSession
from app.users.exceptions import EmailAlreadyRegisteredError
from app.users.model import User
from app.users.repository import UserRepository
from app.users.schemas import UserCreate, UserRead
from app.users.use_cases import RegisterUser

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserCreate,
    session: DatabaseSession,
) -> User:
    try:
        async with session.begin():
            repo = UserRepository(session)
            use_case = RegisterUser(repo)
            created_user = await use_case.execute(user_data)

        return created_user
    except (EmailAlreadyRegisteredError, IntegrityError) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        ) from error
