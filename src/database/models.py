from datetime import datetime
from enum import Enum

from sqlalchemy import Integer, String, Boolean, Date, ForeignKey, func
from sqlalchemy.orm import relationship, DeclarativeBase, mapped_column, Mapped
from sqlalchemy.sql.sqltypes import DateTime


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


class UserRole(str, Enum):
    """User role enumeration."""

    user = "user"
    admin = "admin"


class User(Base):
    """ORM model representing an application user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.user, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="user", cascade="all, delete-orphan"
    )


class Contact(Base):
    """ORM model representing a contact belonging to a user."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    birthday: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="contacts")
