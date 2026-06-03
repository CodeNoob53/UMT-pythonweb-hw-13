"""User-related API routes.

Provides endpoints for retrieving the current user and updating avatars.
"""

from cloudinary.exceptions import Error as CloudinaryError, NotAllowed
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.database.db import get_db
from src.database.models import User, UserRole
from src.schemas import UserResponse
from src.services.auth import get_current_user, require_role, invalidate_user_cache
from src.services.upload_file import UploadFileService
from src.services.users import UserService
from src.conf.config import settings

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=UserResponse, description="No more than 10 requests per minute")
@limiter.limit("10/minute")
async def me(request: Request, user: User = Depends(get_current_user)) -> UserResponse:
    """Return the profile of the currently authenticated user.

    Args:
        request: Incoming HTTP request (required by SlowAPI rate limiter).
        user: Current user resolved from JWT + Redis cache.

    Returns:
        User profile data.
    
    Example:
        curl -H "Authorization: Bearer <access_token>" "{base_url}/users/me"
    """
    return user


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar(
    file: UploadFile = File(),
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Upload a new avatar image for the current user. Admin only.

    Regular users receive 403 Forbidden.

    Args:
        file: The image file to upload.
        current_user: Admin user resolved from JWT dependency.
        db: Async DB session.

    Raises:
        HTTPException 400: If no file is provided or it is not an image.
        HTTPException 403: If the user is not an admin, or Cloudinary rejects the upload.
        HTTPException 502: If Cloudinary upload fails for another reason.

    Returns:
        Updated user profile with new avatar URL.

    Example:
        curl -X PATCH "{base_url}/users/avatar" -H "Authorization: Bearer <access_token>" \
            -F "file=@/path/to/avatar.jpg"
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Avatar file is required"
        )
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Avatar must be an image"
        )

    try:
        avatar_url = UploadFileService(
            settings.CLD_NAME, settings.CLD_API_KEY, settings.CLD_API_SECRET
        ).upload_file(file, current_user.username)
    except NotAllowed as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cloudinary credentials do not allow avatar uploads",
        ) from err
    except CloudinaryError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not upload avatar to Cloudinary",
        ) from err

    user_service = UserService(db)
    updated = await user_service.update_avatar_url(current_user.email, avatar_url)
    await invalidate_user_cache(current_user.username)
    return updated
