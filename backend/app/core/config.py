from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="HELPDESK_",
        extra="ignore",
    )

    app_name: str = "Helpdesk API"
    app_version: str = "0.1.0"
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    database_url: str = (
        "postgresql+asyncpg://helpdesk:helpdesk_password@localhost:5433/helpdesk"
    )
    jwt_secret_key: SecretStr = SecretStr(
        "development-only-secret-change-in-production"
    )
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(
        default=30,
        gt=0,
    )
    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"

    log_format: Literal[
        "console",
        "json",
    ] = "console"


@lru_cache
def get_settings() -> Settings:
    return Settings()
