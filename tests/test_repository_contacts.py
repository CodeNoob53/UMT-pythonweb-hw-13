import pytest
from datetime import date, timedelta

from src.repository.contacts import ContactRepository
from src.services.users import UserService
from src.schemas import ContactCreate, ContactUpdate
from tests.conftest import TEST_USER


@pytest.mark.asyncio
async def test_contact_crud_and_search(db_session):
    user_service = UserService(db_session)
    user = await user_service.get_user_by_username(TEST_USER["username"])
    repo = ContactRepository(db_session)

    # create
    create = ContactCreate(
        first_name="John",
        last_name="Doe",
        email="jdoe@example.com",
        phone="+123",
        birthday=None,
    )
    contact = await repo.create_contact(create, user)
    assert contact.id

    # get_contacts
    contacts = await repo.get_contacts(user)
    assert any(c.id == contact.id for c in contacts)

    # get_contact
    c = await repo.get_contact(contact.id, user)
    assert c.email == "jdoe@example.com"

    # update
    upd = ContactUpdate(first_name="Jane")
    updated = await repo.update_contact(contact.id, upd, user)
    assert updated.first_name == "Jane"

    # search
    results = await repo.search_contacts(user, "Jane")
    assert any(r.id == contact.id for r in results)

    # delete
    deleted = await repo.delete_contact(contact.id, user)
    assert deleted.id == contact.id
    assert await repo.get_contact(9999, user) is None


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(db_session):
    user_service = UserService(db_session)
    user = await user_service.get_user_by_username(TEST_USER["username"])
    repo = ContactRepository(db_session)

    today = date.today()
    soon = today + timedelta(days=3)
    far = today + timedelta(days=30)

    c1 = ContactCreate(
        first_name="Soon",
        last_name="One",
        email="soon@example.com",
        phone="111",
        birthday=soon,
    )
    c2 = ContactCreate(
        first_name="Later",
        last_name="Two",
        email="later@example.com",
        phone="222",
        birthday=far,
    )

    await repo.create_contact(c1, user)
    await repo.create_contact(c2, user)

    upcoming = await repo.get_upcoming_birthdays(user)
    assert any(x.email == "soon@example.com" for x in upcoming)
    assert all(x.email != "later@example.com" for x in upcoming)
