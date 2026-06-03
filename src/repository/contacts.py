"""Contact repository — data access layer for Contact entities."""

from datetime import date

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas import ContactCreate, ContactUpdate


class ContactRepository:
    """Data access layer for Contact entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with an async DB session."""
        self.db = session

    async def get_contacts(self, user: User, skip: int = 0, limit: int = 100) -> list[Contact]:
        """Return a paginated list of contacts belonging to *user*.

        Args:
            user: The owning user.
            skip: Number of records to skip (offset).
            limit: Maximum number of records to return.

        Returns:
            List of Contact objects.
        """
        stmt = select(Contact).where(Contact.user_id == user.id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_contact(self, contact_id: int, user: User) -> Contact | None:
        """Return a single contact by ID that belongs to *user*, or None.

        Args:
            contact_id: Primary key of the contact.
            user: The owning user.

        Returns:
            Contact object or None if not found.
        """
        stmt = select(Contact).where(Contact.id == contact_id, Contact.user_id == user.id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(self, body: ContactCreate, user: User) -> Contact:
        """Create and persist a new contact for *user*.

        Args:
            body: Validated contact creation payload.
            user: The owning user.

        Returns:
            The newly created Contact.
        """
        contact = Contact(**body.model_dump(), user_id=user.id)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactUpdate, user: User
    ) -> Contact | None:
        """Update an existing contact and return it, or None if not found.

        Args:
            contact_id: Primary key of the contact to update.
            body: Partial update payload (only set fields are applied).
            user: The owning user.

        Returns:
            Updated Contact or None.
        """
        contact = await self.get_contact(contact_id, user)
        if contact is None:
            return None
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(contact, key, value)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Contact | None:
        """Delete a contact and return it, or None if not found.

        Args:
            contact_id: Primary key of the contact to delete.
            user: The owning user.

        Returns:
            The deleted Contact or None.
        """
        contact = await self.get_contact(contact_id, user)
        if contact is None:
            return None
        await self.db.delete(contact)
        await self.db.commit()
        return contact

    async def search_contacts(self, user: User, query: str) -> list[Contact]:
        """Return contacts matching *query* in first name, last name, or email.

        Args:
            user: The owning user.
            query: Case-insensitive search string.

        Returns:
            List of matching Contact objects.
        """
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
        """Return contacts with birthdays in the next 7 days.

        Args:
            user: The owning user.

        Returns:
            List of Contact objects with upcoming birthdays.
        """
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
