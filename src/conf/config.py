from pydantic import ConfigDict, EmailStr, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    DB_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRATION_SECONDS: int = 900
    JWT_REFRESH_EXPIRATION_SECONDS: int = 604800

    REDIS_URL: str
    REDIS_CACHE_TTL: int = 900

    # Comma-separated list of allowed CORS origins.
    # Example: "http://localhost:3000,https://myapp.render.com"
    CORS_ORIGINS: str
    DEMO_BOOTSTRAP_ENABLED: bool = False

    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "Contacts API"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    CLD_NAME: str
    CLD_API_KEY: int
    CLD_API_SECRET: str

    @field_validator("DB_URL", mode="before")
    @classmethod
    def normalize_db_url(cls, value: str) -> str:
        """Use asyncpg when Render provides a standard PostgreSQL URL."""
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    model_config = ConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
