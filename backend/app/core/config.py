from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str

    @field_validator("DATABASE_URL")
    @classmethod
    def _use_asyncpg_driver(cls, value: str) -> str:
        # Railway (and other hosts) hand out plain postgres://.../postgresql://...
        # connection strings, but create_async_engine requires the driver to be
        # explicit. Normalize so every consumer (the app engine, Alembic) gets
        # a URL asyncpg can actually use, without needing the env var itself
        # rewritten per environment.
        if value.startswith("postgres://"):
            value = "postgresql://" + value[len("postgres://") :]
        if value.startswith("postgresql://"):
            value = "postgresql+asyncpg://" + value[len("postgresql://") :]
        return value
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_PRICE_BASIC: str
    STRIPE_PRICE_PRO: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    FRONTEND_URL: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
