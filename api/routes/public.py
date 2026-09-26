from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.deps import get_db
from api.emailer import send_email
from api.models.lead import Lead
from api.ratelimit import check_rate_limit
from api.services.notifications import send_demo_confirmation
from api.version_info import APP_VERSION

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/public", tags=["public"])


class DemoRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    company: str = Field(..., min_length=2, max_length=160)
    fleet_size: str | None = Field(default=None, max_length=40)
    message: str | None = Field(default=None, max_length=2000)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return request.client.host
    return "unknown"


@router.get("/meta")
async def public_meta() -> dict:
    """Unauthenticated product metadata for the marketing site."""
    return {
        "name": "TerraIQ",
        "version": APP_VERSION,
        "product": "Terrain-aware fuel optimization for highway fleets",
        "pilot_available": True,
        "stripe_configured": bool(settings.stripe_secret_key and settings.stripe_price_pilot_monthly),
    }


@router.post("/demo-request", status_code=202)
async def submit_demo_request(
    body: DemoRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Capture a paid-pilot / demo lead. Rate-limited per IP. Persisted for the founder inbox."""
    await check_rate_limit(f"demo:{_client_ip(request)}", window=3600, limit=8)

    lead = Lead(
        id=str(uuid.uuid4()),
        name=body.name.strip(),
        email=str(body.email),
        company=body.company.strip(),
        fleet_size=body.fleet_size,
        message=body.message,
        source="landing",
        status="new",
        created_at=datetime.now(timezone.utc),
    )
    db.add(lead)
    await db.commit()

    inbox = settings.demo_request_email
    html = (
        f"<p><strong>Name:</strong> {body.name}</p>"
        f"<p><strong>Email:</strong> {body.email}</p>"
        f"<p><strong>Company:</strong> {body.company}</p>"
        f"<p><strong>Fleet size:</strong> {body.fleet_size or '-'}</p>"
        f"<p><strong>Message:</strong></p><p>{(body.message or '-').replace(chr(10), '<br/>')}</p>"
    )
    sent = False
    if inbox:
        sent = await send_email(
            subject=f"TerraIQ pilot request - {body.company}",
            html_body=html,
            to_email=inbox,
        )
    if not sent:
        logger.info(
            "Demo request from %s <%s> at %s (fleet_size=%s): %s",
            body.name,
            body.email,
            body.company,
            body.fleet_size,
            (body.message or "")[:500],
        )
    try:
        await send_demo_confirmation(str(body.email), body.name)
    except Exception:
        logger.exception("Demo confirmation email failed")
    return {"ok": True, "emailed": sent, "lead_id": lead.id}
