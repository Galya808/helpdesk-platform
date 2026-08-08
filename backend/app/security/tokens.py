from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import get_settings
from app.security.exceptions import InvalidAccessTokenError


def create_access_token(
    subject: UUID,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()

    issued_at = datetime.now(UTC)

    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    expires_at = issued_at + expires_delta

    payload = {
        "sub": str(subject),
        "iat": issued_at,
        "exp": expires_at,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> UUID:
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={
                "require": [
                    "sub",
                    "iat",
                    "exp",
                    "type",
                ]
            },
        )

        if payload["type"] != "access":
            raise InvalidAccessTokenError

        subject = payload["sub"]

        if not isinstance(subject, str):
            raise InvalidAccessTokenError

        return UUID(subject)

    except (
        InvalidTokenError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        raise InvalidAccessTokenError from error
