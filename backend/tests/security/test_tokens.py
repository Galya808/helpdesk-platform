from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.core.config import get_settings
from app.security.exceptions import InvalidAccessTokenError
from app.security.tokens import create_access_token, decode_access_token


def test_created_token_is_decoded_into_source_uuid() -> None:
    # Arrange
    subject = uuid4()
    token = create_access_token(subject)

    # Act
    decoded_token = decode_access_token(token)

    # Assert
    assert decoded_token == subject


def test_two_users_get_different_tokens() -> None:
    # Arrange
    subject1 = uuid4()
    subject2 = uuid4()

    # Act
    token1 = create_access_token(subject1)
    token2 = create_access_token(subject2)

    # Assert
    assert token1 != token2


def test_expired_token_raises_invalid_access_token_error() -> None:
    # Arrange
    subject = uuid4()
    token = create_access_token(
        subject,
        expires_delta=timedelta(seconds=-1),
    )

    # Act + Assert
    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)


def test_changed_token_raises_invalid_access_token_error() -> None:
    # Arrange
    subject = uuid4()
    token = create_access_token(subject)
    header, payload, signature = token.split(".")
    changed_first_character = "a" if signature[0] != "a" else "b"
    changed_signature = changed_first_character + signature[1:]

    changed_token = f"{header}.{payload}.{changed_signature}"

    # Act + Assert
    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(changed_token)


def test_token_without_subject_is_rejected() -> None:
    # Arrange
    settings = get_settings()
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=1)

    payload = {
        "iat": issued_at,
        "exp": expires_at,
        "type": "access",
    }

    # Act
    token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    # Assert
    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)


def test_token_with_invalid_subject_is_rejected() -> None:
    # Arrange
    settings = get_settings()
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=1)

    payload = {
        "sub": "invalid-sub",
        "iat": issued_at,
        "exp": expires_at,
        "type": "access",
    }

    # Act
    token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    # Assert
    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)


def test_refresh_token_type_is_rejected_as_access_token() -> None:
    # Arrange
    settings = get_settings()
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=1)

    payload = {
        "sub": str(uuid4()),
        "iat": issued_at,
        "exp": expires_at,
        "type": "refresh",
    }

    # Act
    token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    # Assert
    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)
