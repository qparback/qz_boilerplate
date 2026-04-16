"""
Central application configuration.

All settings come from environment variables (loaded via docker compose env_file
or via the --env-file Makefile flags). pydantic-settings does the parsing.

Required vs optional:
    - DATABASE_URL and API_KEY are required — the app cannot start without them.
    - External-service keys (anthropic, postmark) are optional at startup so that
      the scheduler service (which doesn't use them) can boot in environments
      that haven't filled them in yet. The relevant client classes raise at
      use-time if the key is missing.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_env: str = "dev"
    project_name: str = "myapp"
    log_level: str = "INFO"
    log_to_db: bool = True

    # Database (required)
    database_url: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "myapp"

    # API security (required)
    api_key: str
    admin_ip_whitelist: str = "127.0.0.1"

    # External services (optional — clients fail at use-time if missing)
    anthropic_api_key: str = ""
    postmark_server_token: str = ""
    postmark_from_email: str = ""
    postmark_from_name: str = "MyApp"

    # Scheduler
    scheduler_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def is_dev(self) -> bool:
        return self.app_env == "dev"

    @property
    def is_prod(self) -> bool:
        return self.app_env == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
