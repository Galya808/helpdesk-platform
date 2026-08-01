from pathlib import Path

import pytest

from app.core.config import Settings


def test_settings_have_expected_defaults(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)

    # Act
    settings = Settings()

    # Assert
    assert settings.app_name == "Helpdesk API"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.database_url == (
        "postgresql+asyncpg://helpdesk:helpdesk_password@localhost:5432/helpdesk"
    )


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
