from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db
from api.models.job import Job
from api.models.telemetry_upload import TelemetryUpload
from api.schemas.telemetry import TelemetryLinkBody, TelemetryListPage, TelemetryResponse
from api.services.telemetry_csv import parse_telemetry_csv

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


@router.post("", response_model=TelemetryResponse, status_code=201)
async def upload_telemetry(
    file: UploadFile = File(...),
    job_id: str | None = None,
    corridor_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _user, fleet = current_user
    raw = (await file.read()).decode("utf-8", errors="replace")
    try:
        points, n = parse_telemetry_csv(raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not job_id:
        raise HTTPException(status_code=400, detail="job_id query parameter is required")

    job_row = await db.get(Job, job_id)
    if not job_row or job_row.fleet_id != fleet.id:
        raise HTTPException(status_code=404, detail="Job not found")

    if corridor_id:
        from api.models.saved_corridor import SavedCorridor  # noqa: PLC0415

        cor = await db.get(SavedCorridor, corridor_id)
        if not cor or cor.fleet_id != fleet.id:
            raise HTTPException(status_code=404, detail="Corridor not found")

    up = TelemetryUpload(
        id=str(uuid.uuid4()),
        fleet_id=fleet.id,
        job_id=job_id,
        corridor_id=corridor_id,
        original_filename=file.filename or "telemetry.csv",
        row_count=n,
        points=points,
        status="pending",
    )
    db.add(up)
    await db.commit()
    await db.refresh(up)

    from api.workers.tasks import process_telemetry_upload  # noqa: PLC0415

    process_telemetry_upload.delay(up.id)
    return up


@router.get("", response_model=TelemetryListPage)
async def list_telemetry(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _user, fleet = current_user
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    cond = TelemetryUpload.fleet_id == fleet.id
    total = (await db.execute(select(func.count()).select_from(TelemetryUpload).where(cond))).scalar_one()
    res = await db.execute(
        select(TelemetryUpload)
        .where(cond)
        .order_by(desc(TelemetryUpload.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list(res.scalars().all())
    return TelemetryListPage(
        items=[TelemetryResponse.model_validate(r) for r in rows],
        total=int(total),
        page=page,
        page_size=page_size,
    )


@router.get("/{upload_id}", response_model=TelemetryResponse)
async def get_telemetry(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _user, fleet = current_user
    row = await db.get(TelemetryUpload, upload_id)
    if not row or row.fleet_id != fleet.id:
        raise HTTPException(status_code=404, detail="Upload not found")
    return row


@router.patch("/{upload_id}/link", response_model=TelemetryResponse)
async def link_telemetry_job(
    upload_id: str,
    body: TelemetryLinkBody,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Attach or change the related optimization job and re-queue adherence processing."""
    _user, fleet = current_user
    row = await db.get(TelemetryUpload, upload_id)
    if not row or row.fleet_id != fleet.id:
        raise HTTPException(status_code=404, detail="Upload not found")

    job_row = await db.get(Job, body.job_id)
    if not job_row or job_row.fleet_id != fleet.id:
        raise HTTPException(status_code=404, detail="Job not found")

    if body.corridor_id:
        from api.models.saved_corridor import SavedCorridor  # noqa: PLC0415

        cor = await db.get(SavedCorridor, body.corridor_id)
        if not cor or cor.fleet_id != fleet.id:
            raise HTTPException(status_code=404, detail="Corridor not found")
        row.corridor_id = body.corridor_id

    row.job_id = body.job_id
    row.status = "pending"
    row.adherence = None
    row.error_message = None
    row.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(row)

    from api.workers.tasks import process_telemetry_upload  # noqa: PLC0415

    process_telemetry_upload.delay(row.id)
    return row
