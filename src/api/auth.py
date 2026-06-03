"""Authentication API routes.

This module exposes endpoints for registration, login, token refresh,
email confirmation, and password reset.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.schemas import (
    UserCreate,
    UserResponse,
    Token,
    TokenRefreshRequest,
    RequestPasswordReset,
    ConfirmPasswordReset,
    MessageResponse,
)
from src.services.auth import (
    Hash,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_email_from_token,
    verify_password_reset_token,
    invalidate_user_cache,
)
from src.services.email import send_email, send_password_reset_email
from src.services.users import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user and enqueue an email verification send.

    The endpoint hashes the provided password, creates the user record,
    and schedules `send_email` as a background task so the HTTP request
    is not blocked by network I/O.

    Raises:
        HTTPException 409: If the email or username is already taken.

    Returns:
        The created `UserResponse` object (without raw password).
    """
    user_service = UserService(db)

    if await user_service.get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким email вже існує",
        )
    if await user_service.get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким іменем вже існує",
        )

    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)

    background_tasks.add_task(
        send_email, new_user.email, new_user.username, str(request.base_url)
    )
    return new_user


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticate credentials and return an `access_token`/`refresh_token` pair.

    On successful authentication the refresh token is stored in the DB
    for rotation and revocation, and the user cache is invalidated so
    subsequent requests read the latest user state.

    Raises:
        HTTPException 401: If credentials are invalid or the account is unconfirmed.

    Returns:
        A `Token` containing `access_token`, `refresh_token`, and `token_type`.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)
    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильний логін або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Електронна адреса не підтверджена",
        )

    access_token = await create_access_token(data={"sub": user.username})
    refresh_token = await create_refresh_token(data={"sub": user.username})

    await user_service.update_refresh_token(user, refresh_token)
    await invalidate_user_cache(user.username)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_tokens(
    body: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Exchange a valid refresh token for new access + refresh tokens.

    Args:
        body: Request body containing the refresh token.
        db: Async DB session.

    Raises:
        HTTPException 401: If the refresh token is invalid, expired, or revoked.

    Returns:
        New JWT access token, new refresh token, and token type.
    """
    from jose import JWTError, jwt
    from src.conf.config import settings

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            body.refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        token_type: str = payload.get("token_type", "")
        if username is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None or user.refresh_token != body.refresh_token:
        raise credentials_exception

    new_access = await create_access_token(data={"sub": user.username})
    new_refresh = await create_refresh_token(data={"sub": user.username})

    await user_service.update_refresh_token(user, new_refresh)
    await invalidate_user_cache(user.username)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout", response_model=MessageResponse)
async def logout(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> MessageResponse:
    """Revoke the current user's refresh token and clear their cache entry.

    Args:
        db: Async DB session.
        current_user: Authenticated user from JWT.

    Returns:
        Confirmation message.
    """
    user_service = UserService(db)
    await user_service.update_refresh_token(current_user, None)
    await invalidate_user_cache(current_user.username)
    return {"message": "Logged out successfully"}


@router.get("/confirmed_email/{token}", response_model=MessageResponse)
async def confirmed_email(
    token: str, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """Confirm a user's email address using a verification token.

    Args:
        token: JWT email-verification token from the confirmation link.
        db: Async DB session.

    Raises:
        HTTPException 400: If the user is not found.

    Returns:
        Confirmation message.
    """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    await user_service.confirmed_email(email)
    await invalidate_user_cache(user.username)
    return {"message": "Електронну пошту підтверджено"}


@router.post("/reset-password/request", response_model=MessageResponse)
async def request_password_reset(
    body: RequestPasswordReset,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Send a password reset email if the given address is registered.

    Always returns 200 to avoid leaking whether the email exists.

    Args:
        body: Request body with the user's email.
        background_tasks: FastAPI background tasks runner.
        request: Incoming HTTP request (used to build base URL).
        db: Async DB session.

    Returns:
        Generic confirmation message.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)
    if user:
        background_tasks.add_task(
            send_password_reset_email, user.email, user.username, str(request.base_url)
        )
    return {"message": "If this email is registered, a reset link has been sent."}


@router.post("/reset-password/confirm", response_model=MessageResponse)
async def confirm_password_reset(
    body: ConfirmPasswordReset,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Verify the reset token and update the user's password.

    Args:
        body: Request body containing the reset token and the new password.
        db: Async DB session.

    Raises:
        HTTPException 400: If the token is invalid, expired, or user not found.

    Returns:
        Confirmation message.
    """
    email = await verify_password_reset_token(body.token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User not found"
        )

    hashed = Hash().get_password_hash(body.new_password)
    await user_service.update_password(user, hashed)
    await invalidate_user_cache(user.username)
    return {"message": "Password has been reset successfully"}
