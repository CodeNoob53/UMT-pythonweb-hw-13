"""Contacts API router — CRUD operations for user contacts."""

"""Contacts API routes.

Endpoints for CRUD operations on user contacts and search utilities.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.models import User
from src.repository.contacts import ContactRepository
from src.schemas import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactSearchResponse,
    MessageResponse,
)
from src.services.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=list[ContactResponse])
async def get_contacts(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ContactRepository(db)
    return await repo.get_contacts(user, skip, limit)


@router.get("/search", response_model=ContactSearchResponse)
async def search_contacts(
    q: str = Query(..., min_length=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ContactRepository(db)
    contacts = await repo.search_contacts(user, q)
    return {
        "message": "Contacts found" if contacts else "No contacts found",
        "count": len(contacts),
        "contacts": contacts,
    }


@router.get("/birthdays", response_model=list[ContactResponse])
async def upcoming_birthdays(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ContactRepository(db)
    return await repo.get_upcoming_birthdays(user)


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ContactRepository(db)
    contact = await repo.get_contact(contact_id, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ContactRepository(db)
    return await repo.create_contact(body, user)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    body: ContactUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ContactRepository(db)
    contact = await repo.update_contact(contact_id, body, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", response_model=MessageResponse)
async def delete_contact(
    contact_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ContactRepository(db)
    contact = await repo.delete_contact(contact_id, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return {"message": "Contact deleted successfully"}
