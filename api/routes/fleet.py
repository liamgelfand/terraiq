from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import and_, delete, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db, require_fleet_admin
from api.models.api_key import ApiKey
from api.models.audit_event import AuditEvent
from api.models.fleet_invite import FleetInvite
from api.models.job import Job
from api.models.job_batch import JobBatch
from api.models.saved_corridor import SavedCorridor
from api.models.telemetry_upload import TelemetryUpload
from api.models.user import User
from api.models.webhook_delivery import WebhookDelivery
from api.emailer import send_email
from api.config import settings
from api.schemas.fleet import (
    AuditEventResponse,
    AuditLogPage,
    DataPurgeBody,
    FleetUsageResponse,
    InviteCreateRequest,
    InviteResponse,
    WebhookDeliveryPage,
    WebhookDeliveryResponse,
)
from api.services.audit import record_audit_event

router = APIRouter(prefix="/api/fleet", tags=["fleet"])


@router.post("/invites", response_model=InviteResponse, status_code=201)
async def create_invite(
    body: InviteCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_fleet_admin),
):
    user, fleet = admin
    email_norm = body.email.strip().lower()

    existing = await db.execute(select(User).where(func.lower(User.email) == email_norm))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    exp = datetime.now(timezone.utc) + timedelta(days=7)

    inv = FleetInvite(
        fleet_id=fleet.id,
        email=email_norm,
        token_hash=token_hash,
        invited_by_user_id=user.id,
        expires_at=exp,
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)

    link = f"{settings.public_app_url}/?invite_token={raw}"
    await send_email(
        f"Invitation to join fleet {fleet.name} on TerraIQ",
        f"<p>You were invited to <b>{fleet.name}</b>.</p><p><a href=\"{link}\">Accept invitation</a></p>",
        email_norm,
    )

    await record_audit_event(
        db,
        fleet_id=fleet.id,
        actor_user_id=user.id,
        action="invite.created",
        resource_type="fleet_invite",
        resource_id=inv.id,
        details={"email": email_norm},
    )

    return {
        "id": inv.id,
        "email": inv.email,
        "fleet_id": inv.fleet_id,
        "created_at": inv.created_at,
        "expires_at": inv.expires_at,
    }


@router.get("/audit-events", response_model=AuditLogPage)
async def list_audit_events(
    page: int = 1,
    page_size: int = 25,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_fleet_admin),
) -> AuditLogPage:
    _user, fleet = admin
    page = max(1, page)
    page_size = min(100, max(1, page_size))

    cond = AuditEvent.fleet_id == fleet.id
    total = (
        await db.execute(select(func.count()).select_from(AuditEvent).where(cond))
    ).scalar_one()

    result = await db.execute(
        select(AuditEvent)
        .where(cond)
        .order_by(desc(AuditEvent.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list(result.scalars().all())
    return AuditLogPage(
        items=[AuditEventResponse.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/webhook-deliveries", response_model=WebhookDeliveryPage)
async def list_webhook_deliveries(
    page: int = 1,
    page_size: int = 25,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_fleet_admin),
) -> WebhookDeliveryPage:
    _user, fleet = admin
    page = max(1, page)
    page_size = min(100, max(1, page_size))

    total = (
        await db.execute(
            select(func.count())
            .select_from(WebhookDelivery)
            .join(Job, WebhookDelivery.job_id == Job.id)
            .where(Job.fleet_id == fleet.id)
        )
    ).scalar_one()

    result = await db.execute(
        select(WebhookDelivery)
        .join(Job, WebhookDelivery.job_id == Job.id)
        .where(Job.fleet_id == fleet.id)
        .order_by(desc(WebhookDelivery.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list(result.scalars().all())
    return WebhookDeliveryPage(
        items=[WebhookDeliveryResponse.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/usage", response_model=FleetUsageResponse)
async def fleet_usage(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> FleetUsageResponse:
    user, fleet = current_user
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    jobs_total = (
        await db.execute(select(func.count()).select_from(Job).where(Job.fleet_id == fleet.id))
    ).scalar_one()
    jobs_completed = (
        await db.execute(
            select(func.count())
            .select_from(Job)
            .where(and_(Job.fleet_id == fleet.id, Job.status == "completed"))
        )
    ).scalar_one()
    jobs_failed = (
        await db.execute(
            select(func.count())
            .select_from(Job)
            .where(and_(Job.fleet_id == fleet.id, Job.status == "failed"))
        )
    ).scalar_one()
    jobs_this_month = (
        await db.execute(
            select(func.count())
            .select_from(Job)
            .where(and_(Job.fleet_id == fleet.id, Job.created_at >= month_start))
        )
    ).scalar_one()

    key_usage = (
        await db.execute(select(func.coalesce(func.sum(ApiKey.usage_count), 0)).where(ApiKey.fleet_id == fleet.id))
    ).scalar_one()

    return FleetUsageResponse(
        jobs_total=int(jobs_total),
        jobs_completed=int(jobs_completed),
        jobs_failed=int(jobs_failed),
        jobs_this_month=int(jobs_this_month),
        api_key_usage_total=int(key_usage or 0),
    )


@router.get("/data-export")
async def fleet_data_export(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_fleet_admin),
):
    """JSON bundle of pilot metadata (no raw telemetry points)."""
    user, fleet = admin
    corridors = (
        await db.execute(
            select(SavedCorridor).where(SavedCorridor.fleet_id == fleet.id).order_by(SavedCorridor.name)
        )
    ).scalars().all()
    batches = (
        await db.execute(
            select(JobBatch).where(JobBatch.fleet_id == fleet.id).order_by(desc(JobBatch.created_at)).limit(500)
        )
    ).scalars().all()
    telem = (
        await db.execute(
            select(TelemetryUpload)
            .where(TelemetryUpload.fleet_id == fleet.id)
            .order_by(desc(TelemetryUpload.created_at))
            .limit(500)
        )
    ).scalars().all()
    job_rows = (
        await db.execute(
            select(Job)
            .where(Job.fleet_id == fleet.id)
            .order_by(desc(Job.created_at))
            .limit(500)
        )
    ).scalars().all()

    def corridor_dict(c: SavedCorridor) -> dict:
        return {
            "id": c.id,
            "name": c.name,
            "origin": c.origin,
            "destination": c.destination,
            "vehicle_id": c.vehicle_id,
            "time_budget_fraction": c.time_budget_fraction,
            "created_at": c.created_at.isoformat(),
        }

    def batch_dict(b: JobBatch) -> dict:
        return {
            "id": b.id,
            "name": b.name,
            "status": b.status,
            "summary": b.summary,
            "created_at": b.created_at.isoformat(),
            "completed_at": b.completed_at.isoformat() if b.completed_at else None,
        }

    def telem_dict(t: TelemetryUpload) -> dict:
        return {
            "id": t.id,
            "job_id": t.job_id,
            "corridor_id": t.corridor_id,
            "status": t.status,
            "row_count": t.row_count,
            "adherence": t.adherence,
            "error_message": t.error_message,
            "created_at": t.created_at.isoformat(),
        }

    def job_summary(j: Job) -> dict:
        sv = {}
        if j.status == "completed" and j.result and isinstance(j.result, dict):
            sv = j.result.get("savings") or {}
        return {
            "id": j.id,
            "status": j.status,
            "corridor_id": j.corridor_id,
            "batch_id": j.batch_id,
            "created_at": j.created_at.isoformat(),
            "fuel_saved_liters": sv.get("fuel_saved_liters"),
            "lineage": j.lineage,
            "simulation_engine_version": j.simulation_engine_version,
        }

    return {
        "fleet_id": fleet.id,
        "fleet_name": fleet.name,
        "billing_plan": getattr(fleet, "billing_plan", "free"),
        "data_retention_days": settings.data_retention_days,
        "deployment_profile": settings.deployment_profile,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "corridors": [corridor_dict(c) for c in corridors],
        "job_batches": [batch_dict(b) for b in batches],
        "telemetry_uploads": [telem_dict(t) for t in telem],
        "recent_jobs": [job_summary(j) for j in job_rows],
    }


@router.delete("/data-purge", status_code=204, response_class=Response)
async def fleet_data_purge(
    body: DataPurgeBody,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_fleet_admin),
) -> Response:
    user, fleet = admin
    await db.execute(delete(TelemetryUpload).where(TelemetryUpload.fleet_id == fleet.id))

    if body.include_jobs:
        subq = select(Job.id).where(Job.fleet_id == fleet.id)
        await db.execute(delete(WebhookDelivery).where(WebhookDelivery.job_id.in_(subq)))
        await db.execute(delete(Job).where(Job.fleet_id == fleet.id))
    else:
        await db.execute(
            update(Job)
            .where(Job.fleet_id == fleet.id)
            .values(corridor_id=None, batch_id=None)
        )

    await db.execute(delete(JobBatch).where(JobBatch.fleet_id == fleet.id))
    await db.execute(delete(SavedCorridor).where(SavedCorridor.fleet_id == fleet.id))
    await db.commit()

    await record_audit_event(
        db,
        fleet_id=fleet.id,
        actor_user_id=user.id,
        action="fleet.data_purge",
        resource_type="fleet",
        resource_id=fleet.id,
        details={"include_jobs": body.include_jobs},
    )
    return Response(status_code=204)
