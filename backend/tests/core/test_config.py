from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_have_expected_defaults(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)

    environment_variables = (
        "HELPDESK_APP_NAME",
        "HELPDESK_APP_VERSION",
        "HELPDESK_ENVIRONMENT",
        "HELPDESK_DEBUG",
        "HELPDESK_API_V1_PREFIX",
        "HELPDESK_DATABASE_URL",
        "HELPDESK_JWT_SECRET_KEY",
        "HELPDESK_JWT_ALGORITHM",
        "HELPDESK_ACCESS_TOKEN_EXPIRE_MINUTES",
        "HELPDESK_LOG_LEVEL",
        "HELPDESK_LOG_FORMAT",
    )

    for variable in environment_variables:
        monkeypatch.delenv(variable, raising=False)

    # Act
    settings = Settings()

    # Assert
    assert settings.app_name == "Helpdesk API"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.database_url == (
        "postgresql+asyncpg://helpdesk:helpdesk_password@localhost:5433/helpdesk"
    )
    assert (
        settings.jwt_secret_key.get_secret_value()
        == "development-only-secret-change-in-production"
    )
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30
    assert settings.log_level == "INFO"
    assert settings.log_format == "console"


def test_environment_variable_overrides_app_name(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HELPDESK_APP_NAME", "Test Helpdesk API")

    # Act
    settings = Settings()

    # Assert
    assert settings.app_name == "Test Helpdesk API"


def test_environment_variable_overrides_database_url(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(
        "HELPDESK_DATABASE_URL",
        "postgresql+asyncpg://test:test@localhost:5432/test",
    )

    # Act
    settings = Settings()

    # Assert
    assert settings.database_url == (
        "postgresql+asyncpg://test:test@localhost:5432/test"
    )


def test_debug_environment_variable_is_converted_to_boolean(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HELPDESK_DEBUG", "true")

    # Act
    settings = Settings()

    # Assert
    assert settings.debug is True


def test_environment_variables_overrides_jwt_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(
        "HELPDESK_JWT_SECRET_KEY",
        "secret_key",
    )
    monkeypatch.setenv(
        "HELPDESK_JWT_ALGORITHM",
        "HS256",
    )
    monkeypatch.setenv(
        "HELPDESK_ACCESS_TOKEN_EXPIRE_MINUTES",
        "60",
    )

    # Act
    settings = Settings()

    # Assert
    assert settings.jwt_secret_key.get_secret_value() == "secret_key"
    assert settings.jwt_algorithm == "HS256"
    assert isinstance(settings.access_token_expire_minutes, int)
    assert settings.access_token_expire_minutes == 60


@pytest.mark.parametrize("invalid_minutes", [0, -1])
def test_helpdesk_access_token_expire_minutes_are_invalid(
    invalid_minutes: int,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(
        "HELPDESK_ACCESS_TOKEN_EXPIRE_MINUTES",
        str(invalid_minutes),
    )

    # Act + Assert
    with pytest.raises(ValidationError):
        Settings()


def test_unsupported_jwt_algorithm_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(
        "HELPDESK_JWT_ALGORITHM",
        "none",
    )

    # Act + Assert
    with pytest.raises(ValidationError):
        Settings()


def test_jwt_secret_is_hidden_in_settings_representation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    secret = "secret-that-must-not-appear"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(
        "HELPDESK_JWT_SECRET_KEY",
        secret,
    )

    # Act
    settings = Settings()

    # Assert
    assert secret not in repr(settings)
    assert "**********" in repr(settings.jwt_secret_key)


def test_environment_variables_override_logging_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)

    log_level = "DEBUG"
    monkeypatch.setenv(
        "HELPDESK_LOG_LEVEL",
        log_level,
    )

    log_format = "json"
    monkeypatch.setenv(
        "HELPDESK_LOG_FORMAT",
        log_format,
    )

    # Act
    settings = Settings()

    # Assert
    assert settings.log_level == log_level
    assert settings.log_format == log_format


@pytest.mark.parametrize(
    "log_level",
    [
        "TRACE",
        "INVALID",
        "",
    ],
)
def test_invalid_log_level_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    log_level: str,
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)

    monkeypatch.setenv(
        "HELPDESK_LOG_LEVEL",
        log_level,
    )

    # Act + Assert
    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize(
    "log_format",
    [
        "xml",
        "text",
        "",
    ],
)
def test_invalid_log_format_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    log_format: str,
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(
        "HELPDESK_LOG_FORMAT",
        log_format,
    )

    # Act + Assert
    with pytest.raises(ValidationError):
        Settings()
