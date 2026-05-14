"""Transactional email via Resend (https://resend.com). Falls back to logging when not configured."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from api.config import settings

logger = logging.getLogger(__name__)

RESEND_API = "https://api.resend.com/emails"


async def send_email(subject: str, html_body: str, to_email: str) -> bool:
    """
    Send email via Resend. Returns True if sent, False if skipped (no API key) or failed.
    On failure, logs the error but does not raise — password reset still succeeds logically.
    """
    if not settings.resend_api_key:
        logger.info(
            "RESEND_API_KEY not set; email not sent to %s (subject: %s)",
            to_email,
            subject,
        )
        return False

    payload: dict[str, Any] = {
        "from": settings.email_from,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                RESEND_API,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
            )
            if r.status_code >= 400:
                logger.error(
                    "Resend API error %s: %s",
                    r.status_code,
                    r.text[:500],
                )
                return False
    except Exception:
        logger.exception("Failed to send email via Resend")
        return False

    logger.info("Transactional email sent to %s", to_email)
    return True


def send_email_sync(subject: str, html_body: str, to_email: str) -> bool:
    """Sync send for Celery workers (httpx sync client)."""
    if not settings.resend_api_key:
        logger.info(
            "RESEND_API_KEY not set; sync email not sent to %s (subject: %s)",
            to_email,
            subject,
        )
        return False

    payload: dict[str, Any] = {
        "from": settings.email_from,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                RESEND_API,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
            )
            if r.status_code >= 400:
                logger.error(
                    "Resend API error %s: %s",
                    r.status_code,
                    r.text[:500],
                )
                return False
    except Exception:
        logger.exception("Failed to send sync email via Resend")
        return False

    logger.info("Sync transactional email sent to %s", to_email)
    return True
