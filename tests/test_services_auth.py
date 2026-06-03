"""Unit tests for auth service helpers."""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from src.services.auth import (
    Hash,
    create_access_token,
    create_refresh_token,
    create_email_token,
    create_password_reset_token,
    get_email_from_token,
    verify_password_reset_token,
    invalidate_user_cache,
    _cache_user,
)
from src.database.models import User, UserRole


class TestHash:
    def test_hash_and_verify(self):
        h = Hash()
        hashed = h.get_password_hash("mypassword")
        assert h.verify_password("mypassword", hashed)

    def test_wrong_password_fails(self):
        h = Hash()
        hashed = h.get_password_hash("correct")
        assert not h.verify_password("wrong", hashed)

    def test_invalid_hash_returns_false(self):
        h = Hash()
        assert not h.verify_password("any", "not_a_valid_hash")


class TestAccessToken:
    async def test_creates_token_with_access_type(self):
        from jose import jwt
        from src.conf.config import settings

        token = await create_access_token({"sub": "alice"})
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == "alice"
        assert payload["token_type"] == "access"

    async def test_custom_expiry(self):
        from jose import jwt
        from src.conf.config import settings

        token = await create_access_token({"sub": "alice"}, expires_delta=60)
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == "alice"


class TestRefreshToken:
    async def test_creates_token_with_refresh_type(self):
        from jose import jwt
        from src.conf.config import settings

        token = await create_refresh_token({"sub": "bob"})
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert payload["token_type"] == "refresh"


class TestEmailToken:
    async def test_get_email_from_valid_token(self):
        token = create_email_token({"sub": "user@example.com"})
        email = await get_email_from_token(token)
        assert email == "user@example.com"

    async def test_get_email_from_invalid_token_raises(self):
        with pytest.raises(HTTPException) as exc:
            await get_email_from_token("garbage.token.here")
        assert exc.value.status_code in (422, 422)


class TestPasswordResetToken:
    async def test_valid_token_returns_email(self):
        token = create_password_reset_token("reset@example.com")
        email = await verify_password_reset_token(token)
        assert email == "reset@example.com"

    async def test_wrong_token_type_raises(self):
        wrong = await create_access_token({"sub": "reset@example.com"})
        with pytest.raises(HTTPException) as exc:
            await verify_password_reset_token(wrong)
        assert exc.value.status_code == 400

    async def test_invalid_token_raises(self):
        with pytest.raises(HTTPException) as exc:
            await verify_password_reset_token("not.a.token")
        assert exc.value.status_code == 400


class TestCacheUser:
    async def test_cache_does_not_store_password(self, fake_redis):
        from src.services import redis_cache

        user = User(
            id=1,
            username="cachetest",
            email="cache@example.com",
            hashed_password="secret_hash",
            avatar=None,
            confirmed=True,
            role=UserRole.user,
            refresh_token="some_refresh",
        )
        import datetime
        user.created_at = datetime.datetime.now(datetime.UTC)

        await _cache_user(user)

        import json
        raw = await fake_redis.get("user:cachetest")
        assert raw is not None
        data = json.loads(raw)
        assert data["hashed_password"] == ""
        assert data["refresh_token"] is None
        assert data["username"] == "cachetest"
