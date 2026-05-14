from __future__ import annotations

import csv
import io
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, cast, desc, func, select
from sqlalchemy import String as SAString
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db
from api.models.job import Job
from api.schemas.job import JobCreate, JobListPage, JobResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(
    body: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Job:
    user, fleet = current_user
    if body.corridor_id:
        from api.models.saved_corridor import SavedCorridor  # noqa: PLC0415

        cor = await db.get(SavedCorridor, body.corridor_id)
        if not cor or cor.fleet_id != fleet.id:
            raise HTTPException(status_code=404, detail="Corridor not found")
    job = Job(
        id=str(uuid.uuid4()),
        fleet_id=fleet.id,
        status="pending",
        config=body.config.model_dump(),
        corridor_id=body.corridor_id,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    from api.workers.tasks import run_simulation, run_sweep  # noqa: PLC0415

    if body.config.job_type == "sweep":
        run_sweep.delay(job.id)
    else:
        run_simulation.delay(job.id)
    return job


@router.get("", response_model=JobListPage)
async def list_jobs(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> JobListPage:
    user, fleet = current_user
    page = max(1, page)
    page_size = min(100, max(1, page_size))

    conds = [Job.fleet_id == fleet.id]
    if status:
        conds.append(Job.status == status)
    if q and q.strip():
        needle = f"%{q.strip().lower()}%"
        conds.append(
            func.lower(cast(Job.config, SAString)).like(needle),
        )

    combined = and_(*conds)

    total = (await db.execute(select(func.count()).select_from(Job).where(combined))).scalar_one()

    result = await db.execute(
        select(Job)
        .where(combined)
        .order_by(desc(Job.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list(result.scalars().all())
    return JobListPage(
        items=[JobResponse.model_validate(r) for r in rows],
        total=int(total),
        page=page,
        page_size=page_size,
    )


@router.get("/export.csv")
async def export_jobs_csv(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """CSV export of recent jobs for the authenticated fleet (max 500 rows)."""
    user, fleet = current_user
    result = await db.execute(
        select(Job)
        .where(Job.fleet_id == fleet.id)
        .order_by(desc(Job.created_at))
        .limit(500)
    )
    jobs = list(result.scalars().all())

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id",
        "status",
        "created_at",
        "completed_at",
        "job_type",
        "origin",
        "destination",
        "vehicle_id",
        "fuel_saved_liters",
        "fuel_saved_pct",
        "cost_saved_usd",
        "error_code",
        "error_message",
    ])
    for job in jobs:
        cfg = dict(job.config or {})
        savings = (job.result or {}).get("savings") or {} if job.status == "completed" else {}
        writer.writerow([
            job.id,
            job.status,
            job.created_at.isoformat() if job.created_at else "",
            job.completed_at.isoformat() if job.completed_at else "",
            cfg.get("job_type", "optimize"),
            cfg.get("origin", ""),
            cfg.get("destination", ""),
            cfg.get("vehicle_id", ""),
            savings.get("fuel_saved_liters", "") if savings else "",
            savings.get("fuel_saved_pct", "") if savings else "",
            savings.get("cost_saved_usd", "") if savings else "",
            job.error_code or "",
            (job.error_message or "").replace("\n", " ")[:500],
        ])

    data = buf.getvalue()
    return StreamingResponse(
        iter([data]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="terraiq-jobs-export.csv"',
        },
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Job:
    user, fleet = current_user
    job = await db.get(Job, job_id)
    if not job or job.fleet_id != fleet.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
