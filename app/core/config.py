"""Application settings loaded from environment variables.

Secrets are never hardcoded. Values come from `.env`
via pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """PostgreSQL connection settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "proyecto_1"
    db_user: str = "postgres"
    db_password: str = ""

    @property
    def database_url(self) -> str:
        """Build a psycopg2 SQLAlchemy URL from env vars."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
