from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, UserRole
from src.schemas import UserCreate


class UserRepository:
    """Data access layer for User entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with an async DB session."""
        self.db = session

    async def get_user_by_email(self, email: str) -> User | None:
        """Return a user by email, or None if not found."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """Return a user by username, or None if not found."""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, body: UserCreate, avatar: str | None = None) -> User:
        """Create and persist a new regular user."""
        user = User(
            username=body.username,
            email=body.email,
            hashed_password=body.password,
            avatar=avatar,
            role=UserRole.user,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def upsert_demo_user(
        self,
        username: str,
        email: str,
        hashed_password: str,
        role: UserRole,
        avatar: str | None = None,
    ) -> User:
        """Create or reset a confirmed demo user for deployment testing."""
        user = await self.get_user_by_username(username)
        if user is None:
            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                avatar=avatar,
                confirmed=True,
                role=role,
            )
            self.db.add(user)
        else:
            user.email = email
            user.hashed_password = hashed_password
            user.avatar = avatar
            user.confirmed = True
            user.role = role
            user.refresh_token = None

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirmed_email(self, email: str) -> None:
        """Mark the user's email as confirmed."""
        user = await self.get_user_by_email(email)
        user.confirmed = True
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        """Update a user's avatar URL and return the updated user."""
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_refresh_token(self, user: User, token: str | None) -> None:
        """Store or clear a user's refresh token."""
        user.refresh_token = token
        await self.db.commit()

    async def update_password(self, user: User, hashed_password: str) -> None:
        """Update a user's hashed password and clear the refresh token."""
        user.hashed_password = hashed_password
        user.refresh_token = None
        await self.db.commit()
