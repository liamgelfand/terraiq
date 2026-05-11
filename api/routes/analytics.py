from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from api.deps import get_current_user, get_db
from api.models.job import Job

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    user, fleet = current_user

    result = await db.execute(
        select(Job).where(Job.fleet_id == fleet.id, Job.status == "completed")
    )
    completed_jobs = list(result.scalars().all())

    total_result = await db.execute(
        select(func.count()).select_from(Job).where(Job.fleet_id == fleet.id)
    )
    total_jobs = total_result.scalar() or 0

    fuel_saved_L = 0.0
    cost_saved_usd = 0.0
    co2_saved_kg = 0.0
    distance_km = 0.0

    for job in completed_jobs:
        if not job.result:
            continue
        savings = job.result.get("savings", {})
        fuel_saved_L += savings.get("fuel_saved_liters", 0) or 0
        cost_saved_usd += savings.get("cost_saved_usd", 0) or 0
        co2_saved_kg += savings.get("co2_saved_kg", 0) or 0
        opt = job.result.get("optimized", {})
        distance_km += opt.get("total_distance_km", 0) or 0

    return {
        "total_jobs": total_jobs,
        "completed_jobs": len(completed_jobs),
        "total_fuel_saved_L": round(fuel_saved_L, 2),
        "total_cost_saved_usd": round(cost_saved_usd, 2),
        "total_co2_saved_kg": round(co2_saved_kg, 2),
        "total_distance_km": round(distance_km, 2),
    }
