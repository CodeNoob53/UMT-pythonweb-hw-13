from src.conf.config import Settings


def make_settings(db_url: str) -> Settings:
    """Build settings with explicit values for config-specific tests."""
    return Settings(
        DB_URL=db_url,
        JWT_SECRET="x" * 32,
        REDIS_URL="redis://localhost:6379/0",
        CORS_ORIGINS="http://localhost:3000",
        MAIL_USERNAME="test@example.com",
        MAIL_PASSWORD="password",
        MAIL_FROM="test@example.com",
        CLD_NAME="cloud",
        CLD_API_KEY=123,
        CLD_API_SECRET="secret",
    )


def test_settings_normalizes_render_postgres_url():
    settings = make_settings("postgresql://user:pass@host:5432/db")

    assert settings.DB_URL == "postgresql+asyncpg://user:pass@host:5432/db"


def test_settings_keeps_asyncpg_postgres_url():
    settings = make_settings("postgresql+asyncpg://user:pass@host:5432/db")

    assert settings.DB_URL == "postgresql+asyncpg://user:pass@host:5432/db"
