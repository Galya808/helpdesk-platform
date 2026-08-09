from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_database_session
from app.security.schemas import AccessTokenResponse
from app.security.tokens import create_access_token
from app.users.exceptions import BlockedUserError, InvalidCredentialsError
from app.users.repository import UserRepository
from app.users.schemas import UserLogin
from app.users.use_cases import AuthenticateUser

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
]


@router.post(
    "/login",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    user_data: UserLogin,
    session: DatabaseSession,
) -> AccessTokenResponse:
    try:
        repo = UserRepository(session)
        use_case = AuthenticateUser(repo)
        authenticated_user = await use_case.execute(user_data)
        access_token = create_access_token(authenticated_user.id)

        access_token_response = AccessTokenResponse(
            access_token=access_token,
        )

        return access_token_response

    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    except BlockedUserError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is blocked",
        ) from error
