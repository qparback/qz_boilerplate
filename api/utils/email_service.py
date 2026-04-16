"""
Postmark email wrapper.

All outbound mail goes through send_email(). Every send (success or failure)
is logged to email_log so support can answer "did the user get the email?".

The Postmark client is created lazily so the app can boot without a token.
"""

import json
import logging

from postmarker.core import PostmarkClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings


logger = logging.getLogger(__name__)


class EmailNotConfiguredError(RuntimeError):
    """Raised when send_email is called without Postmark credentials."""


class EmailService:
    def __init__(self) -> None:
        self._client: PostmarkClient | None = None

    def _get_client(self) -> PostmarkClient:
        if self._client is None:
            if not settings.postmark_server_token:
                raise EmailNotConfiguredError(
                    "POSTMARK_SERVER_TOKEN is not set — cannot send email"
                )
            if not settings.postmark_from_email:
                raise EmailNotConfiguredError(
                    "POSTMARK_FROM_EMAIL is not set — cannot send email"
                )
            self._client = PostmarkClient(server_token=settings.postmark_server_token)
        return self._client

    async def send_email(
        self,
        db: AsyncSession,
        to: str,
        subject: str,
        html_body: str,
        email_type: str,
        metadata: dict | None = None,
        text_body: str | None = None,
    ) -> bool:
        """Send an email via Postmark and log the attempt to email_log."""
        postmark_id: str | None = None
        status_str = "failed"
        error_message: str | None = None

        try:
            client = self._get_client()
            response = client.emails.send(
                From=f"{settings.postmark_from_name} <{settings.postmark_from_email}>",
                To=to,
                Subject=subject,
                HtmlBody=html_body,
                TextBody=text_body or "Please view this email in an HTML-capable client.",
                MessageStream="outbound",
            )
            postmark_id = response.get("MessageID")
            status_str = "sent"
            logger.info("Email sent to %s (type=%s, id=%s)", to, email_type, postmark_id)
        except Exception as exc:
            error_message = str(exc)
            logger.error("Email failed to %s (type=%s): %s", to, email_type, error_message)
        finally:
            await self._log(
                db=db,
                email_type=email_type,
                recipient=to,
                subject=subject,
                postmark_id=postmark_id,
                status_str=status_str,
                error_message=error_message,
                metadata=metadata,
            )

        return status_str == "sent"

    async def _log(
        self,
        db: AsyncSession,
        email_type: str,
        recipient: str,
        subject: str,
        postmark_id: str | None,
        status_str: str,
        error_message: str | None,
        metadata: dict | None,
    ) -> None:
        await db.execute(
            text(
                """
                INSERT INTO email_log
                    (email_type, recipient_email, subject, postmark_message_id,
                     status, error_message, metadata)
                VALUES
                    (:type, :recipient, :subject, :postmark_id,
                     :status, :error, :metadata)
                """
            ),
            {
                "type": email_type,
                "recipient": recipient,
                "subject": subject,
                "postmark_id": postmark_id,
                "status": status_str,
                "error": error_message,
                "metadata": json.dumps(metadata) if metadata else None,
            },
        )


email_service = EmailService()
