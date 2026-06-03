"""Unit tests for UserRepository."""

import pytest

from src.database.models import User, UserRole
from src.repository.users import UserRepository
from src.schemas import UserCreate
from tests.conftest import TEST_USER, TEST_ADMIN


class TestGetUserByEmail:
    async def test_returns_existing_user(self, db_session):
        repo = UserRepository(db_session)
        user = await repo.get_user_by_email(TEST_USER["email"])
        assert user is not None
        assert user.email == TEST_USER["email"]

    async def test_returns_none_for_unknown_email(self, db_session):
        repo = UserRepository(db_session)
        user = await repo.get_user_by_email("nobody@example.com")
        assert user is None


class TestGetUserByUsername:
    async def test_returns_existing_user(self, db_session):
        repo = UserRepository(db_session)
        user = await repo.get_user_by_username(TEST_USER["username"])
        assert user is not None
        assert user.username == TEST_USER["username"]

    async def test_returns_none_for_unknown_username(self, db_session):
        repo = UserRepository(db_session)
        user = await repo.get_user_by_username("ghost")
        assert user is None


class TestConfirmedEmail:
    async def test_confirm_sets_flag(self, db_session):
        repo = UserRepository(db_session)
        # Create a temporary unconfirmed user
        body = UserCreate(
            username="unconfirmed_unit",
            email="unconfirmed_unit@example.com",
            password="hashed_already",
        )
        new_user = await repo.create_user(body)
        assert not new_user.confirmed

        await repo.confirmed_email(new_user.email)
        refreshed = await repo.get_user_by_email(new_user.email)
        assert refreshed.confirmed is True


class TestUpdateAvatarUrl:
    async def test_updates_avatar(self, db_session):
        repo = UserRepository(db_session)
        new_url = "https://cdn.example.com/new_avatar.png"
        user = await repo.update_avatar_url(TEST_USER["email"], new_url)
        assert user.avatar == new_url


class TestUpdateRefreshToken:
    async def test_stores_and_clears_token(self, db_session):
        repo = UserRepository(db_session)
        user = await repo.get_user_by_username(TEST_USER["username"])
        await repo.update_refresh_token(user, "some_refresh_token")
        updated = await repo.get_user_by_username(TEST_USER["username"])
        assert updated.refresh_token == "some_refresh_token"

        await repo.update_refresh_token(user, None)
        cleared = await repo.get_user_by_username(TEST_USER["username"])
        assert cleared.refresh_token is None


class TestUpdatePassword:
    async def test_updates_password_and_clears_token(self, db_session):
        repo = UserRepository(db_session)
        user = await repo.get_user_by_username(TEST_USER["username"])
        # pre-set a refresh token so we can verify it's cleared
        await repo.update_refresh_token(user, "existing_token")

        new_hash = "new_bcrypt_hash"
        await repo.update_password(user, new_hash)
        refreshed = await repo.get_user_by_username(TEST_USER["username"])
        assert refreshed.hashed_password == new_hash
        assert refreshed.refresh_token is None


class TestCreateUser:
    async def test_role_assignment(self, db_session):
        """Second user created in a non-empty DB gets the 'user' role."""
        repo = UserRepository(db_session)
        body = UserCreate(
            username="newbie",
            email="newbie@example.com",
            password="hashed_pass",
        )
        user = await repo.create_user(body)
        # DB already has records, so role should be 'user'
        assert user.role == UserRole.user
