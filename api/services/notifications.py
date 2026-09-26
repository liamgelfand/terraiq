"""Product emails. All senders swallow errors — the product must keep working without Resend."""
from __future__ import annotations

import logging
from typing import Any

from api.config import settings
from api.emailer import send_email, send_email_sync

logger = logging.getLogger(__name__)


def _app_url() -> str:
    return settings.public_app_url.rstrip("/")


async def send_welcome_email(to_email: str, full_name: str, fleet_name: str) -> None:
    html = (
        f"<p>Hi {full_name},</p>"
        f"<p>Your TerraIQ trial for <strong>{fleet_name}</strong> is ready. "
        "Two mountain corridors are already on the Corridors page.</p>"
        "<ol>"
        "<li>Open a corridor and run an optimization.</li>"
        "<li>Print the driver brief from the Ops board.</li>"
        "<li>Upload a GPS/speed CSV after a trip to score adherence.</li>"
        "</ol>"
        f'<p><a href="{_app_url()}/?auth=login">Sign in</a></p>'
        "<p>Simulated liters are a planning number. Measure fuel on the truck before you scale.</p>"
    )
    await send_email("Welcome to TerraIQ", html, to_email)


async def send_demo_confirmation(to_email: str, name: str) -> None:
    html = (
        f"<p>Hi {name},</p>"
        "<p>We received your TerraIQ pilot request. A human will follow up at this address.</p>"
        "<p>Meanwhile you can create a trial account and run a named corridor yourself.</p>"
        f'<p><a href="{_app_url()}/?auth=register">Create a trial</a></p>'
    )
    await send_email("We got your TerraIQ pilot request", html, to_email)


def notify_job_finished_sync(
    *,
    to_email: str,
    origin: str,
    destination: str,
    status: str,
    savings: dict[str, Any] | None,
    job_id: str,
) -> None:
    if not settings.notify_job_email:
        return
    route = f"{origin} → {destination}"
    extra = ""
    if status == "completed" and savings:
        extra = (
            f"<p>Simulated vs baseline: {savings.get('fuel_saved_liters', '-')} L "
            f"({savings.get('fuel_saved_pct', '-')}%) · "
            f"${savings.get('cost_saved_usd', '-')}.</p>"
            "<p>Not a guarantee. Print the driver brief and measure the truck.</p>"
        )
    html = (
        f"<p>Job {job_id[:8]}… on <strong>{route}</strong> is <strong>{status}</strong>.</p>"
        f"{extra}"
        f'<p><a href="{_app_url()}/">Open TerraIQ</a></p>'
    )
    send_email_sync(f"TerraIQ job {status}: {route}", html, to_email)
