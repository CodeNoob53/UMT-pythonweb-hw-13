"""Shared pytest fixtures for unit and integration tests."""

# Set required env vars BEFORE any src imports so pydantic-settings can validate.
# These are test-only values; the real .env is never read during pytest.
import os as _os
_os.environ.setdefault("DB_URL", "sqlite+aiosqlite:///:memory:")
_os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-only")
_os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
_os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
_os.environ.setdefault("MAIL_USERNAME", "test@example.com")
_os.environ.setdefault("MAIL_PASSWORD", "test")
_os.environ.setdefault("MAIL_FROM", "test@example.com")
_os.environ.setdefault("CLD_NAME", "test")
_os.environ.setdefault("CLD_API_KEY", "0")
_os.environ.setdefault("CLD_API_SECRET", "test")

import asyncio
import sys
from unittest.mock import AsyncMock, patch

import fakeredis.aioredis
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from main import app
from src.database.db import get_db
from src.database.models import Base, User, UserRole
from src.services.auth import Hash, create_access_token, create_refresh_token
from src.services import redis_cache

# ---------------------------------------------------------------------------
# In-memory SQLite database
# ---------------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

# ---------------------------------------------------------------------------
# Test user seed data
# ---------------------------------------------------------------------------
TEST_USER = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "testpassword123",
}

TEST_ADMIN = {
    "username": "adminuser",
    "email": "adminuser@example.com",
    "password": "adminpassword123",
}


# ---------------------------------------------------------------------------
# Database initialisation (once per test module)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module", autouse=True)
def init_db():
    """Create tables, seed a regular user and an admin user."""

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        async with TestingSessionLocal() as session:
            hashed = Hash().get_password_hash(TEST_USER["password"])
            user = User(
                username=TEST_USER["username"],
                email=TEST_USER["email"],
                hashed_password=hashed,
                confirmed=True,
                role=UserRole.user,
                avatar="https://example.com/avatar.png",
            )
            admin_hashed = Hash().get_password_hash(TEST_ADMIN["password"])
            admin = User(
                username=TEST_ADMIN["username"],
                email=TEST_ADMIN["email"],
                hashed_password=admin_hashed,
                confirmed=True,
                role=UserRole.admin,
                avatar="https://example.com/admin_avatar.png",
            )
            session.add_all([user, admin])
            await session.commit()

    asyncio.run(_setup())


# ---------------------------------------------------------------------------
# Fake Redis (in-process, no external Redis required)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module", autouse=True)
def fake_redis():
    """Replace the Redis client with a fakeredis instance for the test session."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    async def _get_fake():
        return fake

    with patch.object(redis_cache, "get_redis", side_effect=_get_fake):
        yield fake


# ---------------------------------------------------------------------------
# FastAPI TestClient
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def client(fake_redis):
    """Return a FastAPI TestClient wired to the in-memory SQLite database."""

    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth token helpers
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture()
async def user_token() -> str:
    """Return a valid JWT access token for the regular test user."""
    return await create_access_token(data={"sub": TEST_USER["username"]})


@pytest_asyncio.fixture()
async def admin_token() -> str:
    """Return a valid JWT access token for the admin test user."""
    return await create_access_token(data={"sub": TEST_ADMIN["username"]})


@pytest_asyncio.fixture()
async def db_session() -> AsyncSession:
    """Yield a database session connected to the in-memory SQLite test database."""
    async with TestingSessionLocal() as session:
        yield session
