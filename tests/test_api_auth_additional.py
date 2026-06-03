"""Additional auth route edge-case tests."""

import pytest
from src.services.auth import create_password_reset_token
from src.database.models import User
from src.services.auth import Hash


def test_confirmed_email_rejects_wrong_token_type(client):
    """A password-reset token must NOT be accepted as an email-verification token."""
    token = create_password_reset_token("noone@example.com")
    resp = client.get(f"/api/auth/confirmed_email/{token}")
    # Fix 2: token_type check now returns 422 instead of reaching the user lookup
    assert resp.status_code == 422


def test_confirm_password_reset_user_not_found(client):
    """A valid reset token for a non-existent user returns 400."""
    token = create_password_reset_token("missing@example.com")
    resp = client.post(
        "/api/auth/reset-password/confirm",
        json={"token": token, "new_password": "abc"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_unconfirmed_user(client, db_session):
    """Login with an unconfirmed email returns 401."""
    hashed = Hash().get_password_hash("pw12345")
    user = User(
        username="unconf",
        email="unconf@example.com",
        hashed_password=hashed,
        confirmed=False,
    )
    async with db_session.begin():
        db_session.add(user)

    resp = client.post(
        "/api/auth/login",
        data={"username": "unconf", "password": "pw12345"},
    )
    assert resp.status_code == 401
    assert "Електронна адреса" in resp.json().get("detail", "")
