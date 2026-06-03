import pytest
from unittest.mock import patch

from src.services.upload_file import UploadFileService


class DummyUpload:
    def __init__(self):
        # mimic FastAPI UploadFile interface with .file attribute
        self.file = b"dummy"


def test_upload_file_success():
    with patch("src.services.upload_file.cloudinary.uploader.upload") as mock_upload, patch(
        "src.services.upload_file.cloudinary.CloudinaryImage"
    ) as MockImage:
        mock_upload.return_value = {"version": 123}
        MockImage.return_value.build_url.return_value = "http://cdn.example/avatar.png"

        svc = UploadFileService("name", 1, "secret")
        url = svc.upload_file(DummyUpload(), "tester")
        assert url == "http://cdn.example/avatar.png"
        mock_upload.assert_called_once()
