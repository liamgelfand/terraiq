from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, require_api_key
from api.models.job import Job

router = APIRouter(prefix="/v1/optimize", tags=["v1"])


# ─── Request / Response schemas ───────────────────────────────────────────────

class VehicleInput(BaseModel):
    type: str = Field(default="freightliner_cascadia")
    load_kg: float | None = Field(
        default=None,
        ge=0,
        le=17_000,
        description="Payload weight in kg (0–17,000 kg). Defaults to full GVW if omitted.",
    )


class OptimizeRequest(BaseModel):
    origin: str = Field(..., description="Origin place name, e.g. 'Denver, CO'")
    destination: str = Field(..., description="Destination place name")
    vehicle: VehicleInput = Field(default_factory=VehicleInput)
    time_budget_fraction: float = Field(
        default=1.05,
        ge=1.0,
        le=2.0,
        description="Allowed travel time as a fraction of baseline (1.05 = 5% longer allowed)",
    )


class SpeedPoint(BaseModel):
    lat: float
    lon: float
    distance_km: float
    recommended_speed_kmh: float
    elevation_m: float


class OptimizeResult(BaseModel):
    distance_km: float
    baseline_fuel_L: float
    optimized_fuel_L: float
    fuel_saved_L: float
    fuel_saved_pct: float
    cost_saved_usd: float
    co2_saved_kg: float
    speed_profile: list[SpeedPoint]


class OptimizeResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    poll_url: str
    result: OptimizeResult | None = None
    error: str | None = None


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_speed_profile(result: dict) -> list[dict]:
    lats = result.get("lat", [])
    lons = result.get("lon", [])
    distances = result.get("distances_m", [])
    speeds = result.get("speed_profile_ms", [])
    elevations = result.get("elevations_m", [])

    points = []
    for i in range(len(lats)):
        points.append({
            "lat": round(lats[i], 6),
            "lon": round(lons[i], 6),
            "distance_km": round(distances[i] / 1000, 3) if i < len(distances) else 0,
            "recommended_speed_kmh": round(speeds[i] * 3.6, 1) if i < len(speeds) else 0,
            "elevation_m": round(elevations[i], 1) if i < len(elevations) else 0,
        })
    return points


def _format_response(job: Job) -> OptimizeResponse:
    base = OptimizeResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        poll_url=f"/v1/optimize/{job.id}",
        error=job.error_message,
    )

    if job.status == "completed" and job.result:
        r = job.result
        savings = r.get("savings", {})
        base.result = OptimizeResult(
            distance_km=round(r["optimized"]["total_distance_km"], 2),
            baseline_fuel_L=round(r["baseline"]["total_fuel_liters"], 3),
            optimized_fuel_L=round(r["optimized"]["total_fuel_liters"], 3),
            fuel_saved_L=round(savings.get("fuel_saved_liters", 0), 3),
            fuel_saved_pct=round(savings.get("fuel_saved_pct", 0), 2),
            cost_saved_usd=round(savings.get("cost_saved_usd", 0), 2),
            co2_saved_kg=round(savings.get("co2_saved_kg", 0), 2),
            speed_profile=_build_speed_profile(r["optimized"]),
        )

    return base


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("", response_model=OptimizeResponse, status_code=202)
async def submit_optimization(
    body: OptimizeRequest,
    db: AsyncSession = Depends(get_db),
    _api_key=Depends(require_api_key),
) -> Any:
    """
    Submit a route optimization job.
    Returns immediately with a job_id and poll_url.
    Poll GET /v1/optimize/{job_id} until status is `completed`.
    """
    config: dict = {
        "origin": body.origin,
        "destination": body.destination,
        "vehicle_id": "freightliner_2022",
        "time_budget_fraction": body.time_budget_fraction,
        "load_kg": body.vehicle.load_kg,
    }

    job = Job(
        id=str(uuid.uuid4()),
        status="pending",
        config=config,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    from api.workers.tasks import run_simulation  # noqa: PLC0415
    run_simulation.delay(job.id)

    return _format_response(job)


@router.get("/{job_id}", response_model=OptimizeResponse)
async def get_optimization(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _api_key=Depends(require_api_key),
) -> Any:
    """Poll for optimization result."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _format_response(job)
