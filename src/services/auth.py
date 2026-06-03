from datetime import datetime, timedelta, UTC
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings
from src.database.db import get_db
from src.database.models import User, UserRole
from src.services.redis_cache import cache_get, cache_set, cache_delete, user_cache_key

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class Hash:
    """Password hashing utilities using bcrypt."""

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Return True if plain_password matches the bcrypt hash."""
        try:
            return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        except ValueError:
            return False

    def get_password_hash(self, password: str) -> str:
        """Return a bcrypt hash of password."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """Create a short-lived JWT access token.

    Args:
        data: Payload dict; must include ``sub`` (username).
        expires_delta: Override TTL in seconds; defaults to settings value.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    ttl = expires_delta if expires_delta else settings.JWT_ACCESS_EXPIRATION_SECONDS
    expire = datetime.now(UTC) + timedelta(seconds=ttl)
    to_encode.update({"exp": expire, "token_type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def create_refresh_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """Create a long-lived JWT refresh token.

    Args:
        data: Payload dict; must include ``sub`` (username).
        expires_delta: Override TTL in seconds; defaults to settings value.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    ttl = expires_delta if expires_delta else settings.JWT_REFRESH_EXPIRATION_SECONDS
    expire = datetime.now(UTC) + timedelta(seconds=ttl)
    to_encode.update({"exp": expire, "token_type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_email_token(data: dict) -> str:
    """Create a 7-day JWT for email verification.

    Args:
        data: Payload dict; must include ``sub`` (email).

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire, "token_type": "email"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_password_reset_token(email: str) -> str:
    """Create a 1-hour JWT for password reset.

    Args:
        email: The user's email address embedded as ``sub``.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(UTC) + timedelta(hours=1)
    payload = {
        "sub": email,
        "exp": expire,
        "token_type": "password_reset",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def get_email_from_token(token: str) -> str:
    """Decode an email-verification JWT and return the email.

    Raises:
        HTTPException 422: If the token is invalid or missing ``sub``.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid token"
            )
        return email
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid token"
        )


async def verify_password_reset_token(token: str) -> str:
    """Decode a password-reset JWT and return the email.

    Raises:
        HTTPException 400: If the token is invalid, expired, or has the wrong type.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("token_type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token"
            )
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token"
            )
        return email
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token is invalid or expired"
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency: validate JWT access token and return the current user.

    Checks Redis cache first; falls back to DB on cache miss and re-populates cache.

    Raises:
        HTTPException 401: If the token is invalid or the user does not exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("token_type", "access")
        if username is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # --- Redis cache lookup ---
    cached = await cache_get(user_cache_key(username))
    if cached is not None:
        # Reconstruct a lightweight User ORM object from the cache dict.
        # Ensure `created_at` is converted back to a datetime if stored as ISO.
        if cached.get("created_at"):
            try:
                cached["created_at"] = datetime.fromisoformat(cached["created_at"])
            except Exception:
                # If parsing fails, leave as-is; the ORM may accept None or string in tests.
                pass
        user = User(**{k: v for k, v in cached.items()})
        return user

    # --- DB fallback ---
    from src.services.users import UserService

    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception

    # Populate cache (never store hashed_password or refresh_token)
    await _cache_user(user)
    return user


async def _cache_user(user: User) -> None:
    """Store safe user fields in Redis with the configured TTL."""
    payload = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar,
        "confirmed": user.confirmed,
        "role": user.role,
        "hashed_password": "",   # intentionally blank — required by ORM constructor
        "refresh_token": None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
    await cache_set(user_cache_key(user.username), payload, settings.REDIS_CACHE_TTL)


async def invalidate_user_cache(username: str) -> None:
    """Remove a user's cache entry from Redis.

    Call this after any mutation (password change, role update, email confirm, etc.).
    """
    await cache_delete(user_cache_key(username))


def require_role(required_role: UserRole):
    """Return a FastAPI dependency that enforces the given minimum role.

    Args:
        required_role: The role the current user must have.

    Returns:
        An async dependency callable.
    """
    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _check
