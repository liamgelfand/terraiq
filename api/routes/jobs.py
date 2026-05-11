from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db
from api.models.job import Job
from api.schemas.job import JobCreate, JobResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(
    body: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Job:
    user, fleet = current_user
    job = Job(
        id=str(uuid.uuid4()),
        fleet_id=fleet.id,
        status="pending",
        config=body.config.model_dump(),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    from api.workers.tasks import run_simulation  # noqa: PLC0415

    run_simulation.delay(job.id)
    return job


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[Job]:
    user, fleet = current_user
    result = await db.execute(
        select(Job)
        .where(Job.fleet_id == fleet.id)
        .order_by(desc(Job.created_at))
        .limit(50)
    )
    return list(result.scalars().all())


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
