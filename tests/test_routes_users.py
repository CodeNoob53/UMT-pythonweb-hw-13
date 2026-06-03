"""Integration tests for /api/users/* routes."""

import io
from unittest.mock import patch, MagicMock

import pytest

from src.services.auth import create_access_token
from tests.conftest import TEST_USER, TEST_ADMIN


class TestGetMe:
    async def test_returns_current_user(self, client, user_token):
        resp = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == TEST_USER["username"]
        assert data["role"] == "user"

    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/api/users/me")
        assert resp.status_code == 401

    async def test_cache_hit_returns_user(self, client, user_token):
        """Second request should hit Redis cache (still returns correct data)."""
        # first call populates cache
        client.get("/api/users/me", headers={"Authorization": f"Bearer {user_token}"})
        # second call hits cache
        resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 200
        assert resp.json()["username"] == TEST_USER["username"]


class TestUpdateAvatar:
    async def test_admin_can_upload_avatar(self, client, admin_token):
        fake_url = "https://cloudinary.com/admin_avatar.png"
        with patch(
            "src.api.users.UploadFileService"
        ) as mock_svc:
            mock_svc.return_value.upload_file.return_value = fake_url
            image_data = io.BytesIO(b"fake image content")
            resp = client.patch(
                "/api/users/avatar",
                headers={"Authorization": f"Bearer {admin_token}"},
                files={"file": ("avatar.png", image_data, "image/png")},
            )
        assert resp.status_code == 200
        assert resp.json()["avatar"] == fake_url

    async def test_regular_user_gets_403(self, client, user_token):
        image_data = io.BytesIO(b"fake image content")
        resp = client.patch(
            "/api/users/avatar",
            headers={"Authorization": f"Bearer {user_token}"},
            files={"file": ("avatar.png", image_data, "image/png")},
        )
        assert resp.status_code == 403

    def test_unauthenticated_gets_401(self, client):
        image_data = io.BytesIO(b"fake image content")
        resp = client.patch(
            "/api/users/avatar",
            files={"file": ("avatar.png", image_data, "image/png")},
        )
        assert resp.status_code == 401
