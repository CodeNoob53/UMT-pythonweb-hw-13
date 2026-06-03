"""Integration tests for /api/auth/* routes."""

import pytest
from unittest.mock import AsyncMock, patch

from src.services.auth import create_access_token, create_refresh_token, create_password_reset_token
from tests.conftest import TEST_USER, TEST_ADMIN


class TestRegister:
    def test_register_new_user(self, client):
        with patch("src.api.auth.send_email", new_callable=AsyncMock):
            resp = client.post(
                "/api/auth/register",
                json={
                    "username": "brandnew",
                    "email": "brandnew@example.com",
                    "password": "password123",
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "brandnew"
        assert "role" in data

    def test_register_duplicate_email(self, client):
        with patch("src.api.auth.send_email", new_callable=AsyncMock):
            resp = client.post(
                "/api/auth/register",
                json={
                    "username": "another_user",
                    "email": TEST_USER["email"],
                    "password": "password123",
                },
            )
        assert resp.status_code == 409

    def test_register_duplicate_username(self, client):
        with patch("src.api.auth.send_email", new_callable=AsyncMock):
            resp = client.post(
                "/api/auth/register",
                json={
                    "username": TEST_USER["username"],
                    "email": "unique123@example.com",
                    "password": "password123",
                },
            )
        assert resp.status_code == 409


class TestLogin:
    def test_login_valid_credentials(self, client):
        resp = client.post(
            "/api/auth/login",
            data={"username": TEST_USER["username"], "password": TEST_USER["password"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        resp = client.post(
            "/api/auth/login",
            data={"username": TEST_USER["username"], "password": "wrongpass"},
        )
        assert resp.status_code == 401

    def test_login_unknown_user(self, client):
        resp = client.post(
            "/api/auth/login",
            data={"username": "nobody", "password": "anything"},
        )
        assert resp.status_code == 401


class TestRefreshToken:
    def test_refresh_returns_new_tokens(self, client):
        # First, login to get a valid refresh token stored in DB
        login_resp = client.post(
            "/api/auth/login",
            data={"username": TEST_USER["username"], "password": TEST_USER["password"]},
        )
        refresh_token = login_resp.json()["refresh_token"]

        resp = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_rejects_invalid_token(self, client):
        resp = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "not.a.valid.jwt"},
        )
        assert resp.status_code == 401

    async def test_refresh_rejects_access_token(self, client):
        """An access token (wrong type) is rejected as refresh token."""
        access = await create_access_token(data={"sub": TEST_USER["username"]})
        resp = client.post("/api/auth/refresh", json={"refresh_token": access})
        assert resp.status_code == 401


class TestLogout:
    async def test_logout_clears_refresh_token(self, client):
        access = await create_access_token(data={"sub": TEST_USER["username"]})
        resp = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully"

    def test_logout_then_refresh_old_token_rejected(self, client):
        """Full flow: login → /users/me (cache) → logout → refresh old token = 401."""
        # 1. Login — get a valid refresh token stored in DB
        login_resp = client.post(
            "/api/auth/login",
            data={"username": TEST_ADMIN["username"], "password": TEST_ADMIN["password"]},
        )
        assert login_resp.status_code == 200
        tokens = login_resp.json()
        access = tokens["access_token"]
        old_refresh = tokens["refresh_token"]

        # 2. Access /users/me (may hit Redis cache)
        me_resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {access}"})
        assert me_resp.status_code == 200

        # 3. Logout — revokes refresh token in DB and clears Redis cache
        logout_resp = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert logout_resp.status_code == 200

        # 4. Try to use old refresh token — must be rejected (DB hash cleared)
        refresh_resp = client.post(
            "/api/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert refresh_resp.status_code == 401


class TestEmailConfirm:
    async def test_already_confirmed(self, client):
        from src.services.auth import create_email_token
        token = create_email_token({"sub": TEST_USER["email"]})
        resp = client.get(f"/api/auth/confirmed_email/{token}")
        assert resp.status_code == 200
        assert "підтверджен" in resp.json()["message"]

    async def test_invalid_token_returns_422(self, client):
        resp = client.get("/api/auth/confirmed_email/bad.token.here")
        assert resp.status_code == 422


class TestPasswordReset:
    def test_request_returns_200_regardless(self, client):
        with patch("src.api.auth.send_password_reset_email", new_callable=AsyncMock):
            resp = client.post(
                "/api/auth/reset-password/request",
                json={"email": TEST_USER["email"]},
            )
        assert resp.status_code == 200

    def test_request_unknown_email_still_200(self, client):
        resp = client.post(
            "/api/auth/reset-password/request",
            json={"email": "ghost@example.com"},
        )
        assert resp.status_code == 200

    async def test_confirm_valid_token(self, client):
        token = create_password_reset_token(TEST_USER["email"])
        resp = client.post(
            "/api/auth/reset-password/confirm",
            json={"token": token, "new_password": "NewSecurePass99"},
        )
        assert resp.status_code == 200
        assert "reset" in resp.json()["message"].lower()

    async def test_confirm_invalid_token(self, client):
        resp = client.post(
            "/api/auth/reset-password/confirm",
            json={"token": "not.a.token", "new_password": "anything"},
        )
        assert resp.status_code == 400

    async def test_confirm_wrong_token_type(self, client):
        # Access token has wrong token_type
        wrong = await create_access_token(data={"sub": TEST_USER["email"]})
        resp = client.post(
            "/api/auth/reset-password/confirm",
            json={"token": wrong, "new_password": "anything"},
        )
        assert resp.status_code == 400
