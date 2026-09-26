from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db
from api.models.job_batch import JobBatch
from api.schemas.batch import BatchCreate, BatchListPage, BatchResponse
from api.services.plans import assert_can_create_jobs

router = APIRouter(prefix="/api/batches", tags=["batches"])


@router.post("", response_model=BatchResponse, status_code=201)
async def create_batch(
    body: BatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user, fleet = current_user
    n = len(body.corridor_ids)
    await assert_can_create_jobs(db, fleet, max(n, 1), actor_email=user.email)
    batch = JobBatch(
        id=str(uuid.uuid4()),
        fleet_id=fleet.id,
        name=body.name.strip() if body.name else None,
        status="pending",
        config={"corridor_ids": body.corridor_ids},
    )
    db.add(batch)
    await db.commit()
    await db.refresh(batch)

    from api.workers.tasks import run_batch  # noqa: PLC0415

    run_batch.delay(batch.id)
    return batch


@router.get("", response_model=BatchListPage)
async def list_batches(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _user, fleet = current_user
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    cond = JobBatch.fleet_id == fleet.id
    total = (await db.execute(select(func.count()).select_from(JobBatch).where(cond))).scalar_one()
    res = await db.execute(
        select(JobBatch)
        .where(cond)
        .order_by(desc(JobBatch.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list(res.scalars().all())
    return BatchListPage(
        items=[BatchResponse.model_validate(r) for r in rows],
        total=int(total),
        page=page,
        page_size=page_size,
    )


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _user, fleet = current_user
    row = await db.get(JobBatch, batch_id)
    if not row or row.fleet_id != fleet.id:
        raise HTTPException(status_code=404, detail="Batch not found")
    return row
