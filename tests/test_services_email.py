import pytest
from unittest.mock import AsyncMock, patch

from src.services.email import send_email, send_password_reset_email
from tests.conftest import TEST_USER


@pytest.mark.asyncio
async def test_send_email_calls_fastmail():
    with patch("src.services.email.FastMail") as MockFM:
        instance = MockFM.return_value
        instance.send_message = AsyncMock()
        await send_email(TEST_USER["email"], TEST_USER["username"], "http://test/")
        instance.send_message.assert_awaited()


@pytest.mark.asyncio
async def test_send_password_reset_calls_fastmail():
    with patch("src.services.email.FastMail") as MockFM:
        instance = MockFM.return_value
        instance.send_message = AsyncMock()
        await send_password_reset_email(TEST_USER["email"], TEST_USER["username"], "http://test/")
        instance.send_message.assert_awaited()
