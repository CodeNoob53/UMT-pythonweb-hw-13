"""Cloudinary file upload service."""

import cloudinary
import cloudinary.uploader


class UploadFileService:
    """Handles avatar uploads to Cloudinary."""

    def __init__(self, cloud_name: str, api_key: int, api_secret: str) -> None:
        """Configure the Cloudinary SDK with the given credentials.

        Args:
            cloud_name: Cloudinary cloud name.
            api_key: Cloudinary API key.
            api_secret: Cloudinary API secret.
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username: str) -> str:
        """Upload a file to Cloudinary and return a cropped 250x250 URL.

        Args:
            file: An :class:`UploadFile` object from FastAPI.
            username: Used as the Cloudinary public ID path segment.

        Returns:
            URL of the uploaded and transformed image.
        """
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
