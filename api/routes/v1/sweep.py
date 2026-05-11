from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, require_api_key
from api.models.job import Job

router = APIRouter(prefix="/v1/sweep", tags=["v1"])


class SweepVehicleInput(BaseModel):
    type: str = Field(default="freightliner_cascadia")
    load_kg: float | None = Field(default=None, ge=0, le=17_000)


class SweepRequest(BaseModel):
    origin: str = Field(..., description="Origin place name")
    destination: str = Field(..., description="Destination place name")
    vehicle: SweepVehicleInput = Field(default_factory=SweepVehicleInput)


class SweepPoint(BaseModel):
    time_budget_fraction: float
    extra_time_min: float
    fuel_saved_L: float
    fuel_saved_pct: float
    cost_saved_usd: float
    co2_saved_kg: float


class SweepResult(BaseModel):
    distance_km: float
    baseline_fuel_L: float
    curve: list[SweepPoint]


class SweepResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    poll_url: str
    result: SweepResult | None = None
    error: str | None = None


def _format_sweep_response(job: Job) -> SweepResponse:
    base = SweepResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        poll_url=f"/v1/sweep/{job.id}",
        error=job.error_message,
    )
    if job.status == "completed" and job.result:
        r = job.result
        base.result = SweepResult(
            distance_km=round(r.get("distance_km", 0), 2),
            baseline_fuel_L=round(r.get("baseline_fuel_L", 0), 3),
            curve=[SweepPoint(**p) for p in r.get("curve", [])],
        )
    return base


@router.post("", response_model=SweepResponse, status_code=202)
async def submit_sweep(
    body: SweepRequest,
    db: AsyncSession = Depends(get_db),
    _api_key=Depends(require_api_key),
) -> Any:
    """
    Submit a Pareto sweep job.
    Runs the optimizer at 6 time budgets to generate a cost-vs-time Pareto curve.
    Poll GET /v1/sweep/{job_id} until status is `completed`.
    """
    config: dict = {
        "job_type": "sweep",
        "origin": body.origin,
        "destination": body.destination,
        "vehicle_id": "freightliner_2022",
        "load_kg": body.vehicle.load_kg,
    }
    job = Job(id=str(uuid.uuid4()), status="pending", config=config)
    db.add(job)
    await db.commit()
    await db.refresh(job)

    from api.workers.tasks import run_sweep  # noqa: PLC0415

    run_sweep.delay(job.id)
    return _format_sweep_response(job)


@router.get("/{job_id}", response_model=SweepResponse)
async def get_sweep(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _api_key=Depends(require_api_key),
) -> Any:
    """Poll for sweep result."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _format_sweep_response(job)
