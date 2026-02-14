from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Messenger Lite"
    debug: bool = True
    api_prefix: str = "/api"

    secret_key: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    database_url: str
    redis_url: str

    allowed_origins: str = Field(default="http://localhost:5173")

    media_dir: str = "media"
    media_url: str = "/media"
    max_image_size_mb: int = 5

    cookie_domain: str | None = None
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    rate_limit_register: int = 5
    rate_limit_login: int = 10
    rate_limit_message: int = 30

    @property
    def allowed_origins_list(self) -> list[str]:
        return [x.strip() for x in self.allowed_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
