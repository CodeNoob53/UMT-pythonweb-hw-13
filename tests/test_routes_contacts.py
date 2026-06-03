"""Integration tests for /api/contacts/* routes."""

import pytest

from tests.conftest import TEST_USER


class TestContactsCRUD:
    async def test_create_and_get_contact(self, client, user_token):
        # Create
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+380991234567",
            "birthday": "1990-05-15",
            "notes": "Test contact",
        }
        resp = client.post(
            "/api/contacts/",
            json=payload,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        contact_id = data["id"]
        assert data["first_name"] == "John"

        # Get single
        resp = client.get(
            f"/api/contacts/{contact_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == contact_id

    async def test_list_contacts(self, client, user_token):
        resp = client.get(
            "/api/contacts/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_update_contact(self, client, user_token):
        # Create a contact first
        payload = {
            "first_name": "Update",
            "last_name": "Me",
            "email": "update.me@example.com",
            "phone": "+380001112233",
        }
        create_resp = client.post(
            "/api/contacts/",
            json=payload,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        contact_id = create_resp.json()["id"]

        resp = client.put(
            f"/api/contacts/{contact_id}",
            json={"first_name": "Updated"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Updated"

    async def test_update_nonexistent_returns_404(self, client, user_token):
        resp = client.put(
            "/api/contacts/99999",
            json={"first_name": "Ghost"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    async def test_delete_contact(self, client, user_token):
        payload = {
            "first_name": "Delete",
            "last_name": "Me",
            "email": "delete.me@example.com",
            "phone": "+380990000001",
        }
        create_resp = client.post(
            "/api/contacts/",
            json=payload,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        contact_id = create_resp.json()["id"]

        resp = client.delete(
            f"/api/contacts/{contact_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"]

    async def test_delete_nonexistent_returns_404(self, client, user_token):
        resp = client.delete(
            "/api/contacts/99999",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    async def test_get_nonexistent_returns_404(self, client, user_token):
        resp = client.get(
            "/api/contacts/99999",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    async def test_search_contacts(self, client, user_token):
        resp = client.get(
            "/api/contacts/search?q=John",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "contacts" in data

    async def test_upcoming_birthdays(self, client, user_token):
        resp = client.get(
            "/api/contacts/birthdays",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_contacts_require_auth(self, client):
        resp = client.get("/api/contacts/")
        assert resp.status_code == 401
