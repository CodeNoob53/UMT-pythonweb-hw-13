import pytest
from src.services.auth import create_password_reset_token
from src.database.models import User
from src.services.auth import Hash


def test_confirmed_email_user_not_found(client):
    # Token for an email that is not in the DB
    token = create_password_reset_token("noone@example.com")
    resp = client.get(f"/api/auth/confirmed_email/{token}")
    assert resp.status_code == 400


def test_confirm_password_reset_user_not_found(client):
    token = create_password_reset_token("missing@example.com")
    resp = client.post(
        "/api/auth/reset-password/confirm",
        json={"token": token, "new_password": "abc"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_unconfirmed_user(client, db_session):
    # create an unconfirmed user directly in DB
    hashed = Hash().get_password_hash("pw12345")
    user = User(username="unconf", email="unconf@example.com", hashed_password=hashed, confirmed=False)
    async with db_session.begin():
        db_session.add(user)

    resp = client.post(
        "/api/auth/login",
        data={"username": "unconf", "password": "pw12345"},
    )
    assert resp.status_code == 401
    assert "Електронна адреса" in resp.json().get("detail", "")
