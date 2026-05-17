"""Application configuration"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration for the Save Service"""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env.mongodb",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Save Service"
    app_version: str = "0.1.0"

    host: str = "127.0.0.1"
    port: int = 8000

    mongodb_uri: str = Field(validation_alias="MONGODB_URI")
    mongodb_db_name: str = Field(validation_alias="MONGODB_DB_NAME")


def get_settings() -> Settings:
    """Cached settings accessor."""
    return Settings()
