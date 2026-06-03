from datetime import date

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas import ContactCreate, ContactUpdate


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(self, user: User, skip: int = 0, limit: int = 100) -> list[Contact]:
        stmt = select(Contact).where(Contact.user_id == user.id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_contact(self, contact_id: int, user: User) -> Contact | None:
        stmt = select(Contact).where(Contact.id == contact_id, Contact.user_id == user.id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(self, body: ContactCreate, user: User) -> Contact:
        contact = Contact(**body.model_dump(), user_id=user.id)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(self, contact_id: int, body: ContactUpdate, user: User) -> Contact | None:
        contact = await self.get_contact(contact_id, user)
        if contact is None:
            return None
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(contact, key, value)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Contact | None:
        contact = await self.get_contact(contact_id, user)
        if contact is None:
            return None
        await self.db.delete(contact)
        await self.db.commit()
        return contact

    async def search_contacts(self, user: User, query: str) -> list[Contact]:
        stmt = select(Contact).where(
            Contact.user_id == user.id,
            or_(
                Contact.first_name.ilike(f"%{query}%"),
                Contact.last_name.ilike(f"%{query}%"),
                Contact.email.ilike(f"%{query}%"),
            ),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_upcoming_birthdays(self, user: User) -> list[Contact]:
        today = date.today()
        contacts = await self.get_contacts(user, skip=0, limit=10000)
        result = []
        for contact in contacts:
            if contact.birthday is None:
                continue
            birthday_this_year = contact.birthday.replace(year=today.year)
            if birthday_this_year < today:
                birthday_this_year = contact.birthday.replace(year=today.year + 1)
            if 0 <= (birthday_this_year - today).days <= 7:
                result.append(contact)
        return result
