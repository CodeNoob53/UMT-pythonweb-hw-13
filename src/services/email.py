"""Email utilities for sending verification and password reset messages.

This module wraps `fastapi-mail` to send templated emails for account
verification and password reset flows.
"""

from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.conf.config import settings
from src.services.auth import create_email_token, create_password_reset_token

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(email: EmailStr, username: str, host: str) -> None:
    """Send an email verification message to a newly registered user.

    Args:
        email: Recipient's email address.
        username: Recipient's display name.
        host: Base URL of the application, used to build the confirmation link.
    """
    try:
        token_verification = create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        print(err)


async def send_password_reset_email(email: EmailStr, username: str, host: str) -> None:
    """Send a password reset link to the user.

    Args:
        email: Recipient's email address.
        username: Recipient's display name.
        host: Base URL of the application, used to build the reset link.
    """
    try:
        token = create_password_reset_token(email)
        message = MessageSchema(
            subject="Password Reset Request",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token,
            },
            subtype=MessageType.html,
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="password_reset.html")
    except ConnectionErrors as err:
        print(err)
