from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.users.exceptions import UserManagementForbiddenError
from app.users.repository import UserRepository
from app.users.schemas import UserListQuery, UserPage
from app.users.use_cases import ListUsers

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

UserQuery = Annotated[
    UserListQuery,
    Depends(),
]


@router.get(
    "/users",
    response_model=UserPage,
)
async def list_users(
    query: UserQuery,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> UserPage:
    try:
        repository = UserRepository(session)
        use_case = ListUsers(repository)

        result = await use_case.execute(
            query=query,
            current_user=current_user,
        )

        return result

    except UserManagementForbiddenError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User management is restricted to administrators",
        ) from error
