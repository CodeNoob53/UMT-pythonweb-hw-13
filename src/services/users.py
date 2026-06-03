import hashlib
import hmac

from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.models import User
from src.repository.users import UserRepository
from src.schemas import UserCreate


def _hash_token(token: str) -> str:
    """Return a SHA-256 hex digest of *token*.

    Used to store refresh tokens safely without persisting the raw JWT.
    SHA-256 is used (not bcrypt) because JWTs exceed bcrypt's 72-byte limit.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_refresh_token_hash(raw_token: str, stored_hash: str | None) -> bool:
    """Return True if the SHA-256 digest of *raw_token* matches *stored_hash*.

    Uses :func:`hmac.compare_digest` to prevent timing attacks.

    Args:
        raw_token: The raw JWT refresh token from the request.
        stored_hash: The SHA-256 hex digest stored in the database.

    Returns:
        True if the token is valid, False otherwise.
    """
    if stored_hash is None:
        return False
    return hmac.compare_digest(_hash_token(raw_token), stored_hash)


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
        """Store a SHA-256 hash of *token* in DB, or clear it if *token* is None.

        The raw JWT is never persisted — only its digest. Use
        :func:`verify_refresh_token_hash` to verify on the next request.

        Note:
            bcrypt is not used here because JWT strings commonly exceed
            bcrypt's 72-byte password limit.
        """
        token_hash = _hash_token(token) if token is not None else None
        return await self.repository.update_refresh_token(user, token_hash)

    async def update_password(self, user: User, hashed_password: str) -> None:
        """Update a user's password hash and revoke the refresh token."""
        return await self.repository.update_password(user, hashed_password)
