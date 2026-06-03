from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.models import User
from src.repository.users import UserRepository
from src.schemas import UserCreate


class UserService:
    """Business logic layer for user operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with an async DB session."""
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate) -> User:
        """Create a new user, auto-generating a Gravatar avatar if possible."""
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception:
            pass
        return await self.repository.create_user(body, avatar)

    async def get_user_by_email(self, email: str) -> User | None:
        """Return a user by email."""
        return await self.repository.get_user_by_email(email)

    async def get_user_by_username(self, username: str) -> User | None:
        """Return a user by username."""
        return await self.repository.get_user_by_username(username)

    async def confirmed_email(self, email: str) -> None:
        """Confirm a user's email address."""
        return await self.repository.confirmed_email(email)

    async def update_avatar_url(self, email: str, url: str) -> User:
        """Update a user's avatar URL."""
        return await self.repository.update_avatar_url(email, url)

    async def update_refresh_token(self, user: User, token: str | None) -> None:
        """Store or revoke a user's refresh token."""
        return await self.repository.update_refresh_token(user, token)

    async def update_password(self, user: User, hashed_password: str) -> None:
        """Update a user's password hash and revoke the refresh token."""
        return await self.repository.update_password(user, hashed_password)
