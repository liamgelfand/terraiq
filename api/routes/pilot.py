from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db
from api.models.job import Job
from api.models.saved_corridor import SavedCorridor
from api.models.telemetry_upload import TelemetryUpload
from api.services.driver_brief import build_driver_brief_from_job_result, render_driver_brief_html

router = APIRouter(prefix="/api/pilot", tags=["pilot"])


class OpsRow(BaseModel):
    corridor_id: str
    corridor_name: str
    origin: str
    destination: str
    last_job_id: str | None
    last_job_status: str | None
    last_job_completed_at: datetime | None
    fuel_saved_liters: float | None
    fuel_saved_pct: float | None
    cost_saved_usd: float | None
    adherence_pct: float | None


@router.get("/ops-board", response_model=list[OpsRow])
async def ops_board(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _user, fleet = current_user
    res = await db.execute(
        select(SavedCorridor)
        .where(SavedCorridor.fleet_id == fleet.id)
        .order_by(SavedCorridor.name)
    )
    corridors = list(res.scalars().all())
    out: list[OpsRow] = []
    for c in corridors:
        jrows = await db.execute(
            select(Job)
            .where(Job.fleet_id == fleet.id, Job.corridor_id == c.id)
            .order_by(desc(Job.created_at))
            .limit(1)
        )
        job = jrows.scalars().first()
        fuel_L = fuel_pct = cost = None
        completed_at = None
        if job and job.status == "completed" and job.result:
            sv = (job.result.get("savings") or {}) if isinstance(job.result, dict) else {}
            fuel_L = sv.get("fuel_saved_liters")
            fuel_pct = sv.get("fuel_saved_pct")
            cost = sv.get("cost_saved_usd")
            completed_at = job.completed_at

        trows = await db.execute(
            select(TelemetryUpload)
            .where(
                TelemetryUpload.fleet_id == fleet.id,
                TelemetryUpload.corridor_id == c.id,
                TelemetryUpload.status == "processed",
            )
            .order_by(desc(TelemetryUpload.created_at))
            .limit(1)
        )
        tel = trows.scalars().first()
        adh = (tel.adherence or {}).get("pct_in_band") if tel else None

        out.append(
            OpsRow(
                corridor_id=c.id,
                corridor_name=c.name,
                origin=c.origin,
                destination=c.destination,
                last_job_id=job.id if job else None,
                last_job_status=job.status if job else None,
                last_job_completed_at=completed_at,
                fuel_saved_liters=fuel_L,
                fuel_saved_pct=fuel_pct,
                cost_saved_usd=cost,
                adherence_pct=adh,
            )
        )
    return out


@router.get("/export-package.csv")
async def export_package_csv(
    days: int = 90,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Jobs, corridors, and latest telemetry adherence summary for pilots."""
    _user, fleet = current_user
    days = max(1, min(days, 366))
    since = datetime.now(timezone.utc) - timedelta(days=days)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "job_id",
        "status",
        "corridor_id",
        "batch_id",
        "created_at",
        "fuel_saved_liters",
        "fuel_saved_pct",
        "simulation_engine_version",
        "origin",
        "destination",
    ])
    jres = await db.execute(
        select(Job)
        .where(Job.fleet_id == fleet.id, Job.created_at >= since)
        .order_by(desc(Job.created_at))
        .limit(2000)
    )
    for job in jres.scalars().all():
        cfg = dict(job.config or {})
        sv = (
            (job.result or {}).get("savings") or {}
            if job.status == "completed" and job.result
            else {}
        )
        writer.writerow([
            job.id,
            job.status,
            job.corridor_id or "",
            job.batch_id or "",
            job.created_at.isoformat() if job.created_at else "",
            sv.get("fuel_saved_liters", ""),
            sv.get("fuel_saved_pct", ""),
            job.simulation_engine_version or "",
            cfg.get("origin", ""),
            cfg.get("destination", ""),
        ])
    writer.writerow([])
    writer.writerow(["telemetry_id", "job_id", "corridor_id", "status", "adherence_pct", "created_at"])
    tres = await db.execute(
        select(TelemetryUpload)
        .where(TelemetryUpload.fleet_id == fleet.id, TelemetryUpload.created_at >= since)
        .order_by(desc(TelemetryUpload.created_at))
        .limit(2000)
    )
    for row in tres.scalars().all():
        pct = (row.adherence or {}).get("pct_in_band") if row.adherence else ""
        writer.writerow([
            row.id,
            row.job_id or "",
            row.corridor_id or "",
            row.status,
            pct,
            row.created_at.isoformat() if row.created_at else "",
        ])

    data = buf.getvalue()
    return StreamingResponse(
        iter([data]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="terraiq-pilot-package.csv"',
        },
    )


@router.get("/jobs/{job_id}/driver-brief")
async def driver_brief(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict[str, Any]:
    _user, fleet = current_user
    job = await db.get(Job, job_id)
    if not job or job.fleet_id != fleet.id:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed" or not job.result:
        raise HTTPException(status_code=400, detail="Job has no completed result yet")
    cfg = dict(job.config or {})
    result = dict(job.result)
    brief = build_driver_brief_from_job_result(result)
    savings = result.get("savings") if isinstance(result.get("savings"), dict) else {}
    return {
        "job_id": job.id,
        "route": f"{cfg.get('origin', '')} → {cfg.get('destination', '')}",
        "origin": cfg.get("origin"),
        "destination": cfg.get("destination"),
        "vehicle_id": cfg.get("vehicle_id"),
        "fleet_name": fleet.name,
        "savings": savings,
        "brief": brief,
        "lineage": job.lineage,
        "simulation_engine_version": job.simulation_engine_version,
        "completed_at": job.completed_at,
    }


@router.get("/jobs/{job_id}/driver-brief.html", response_class=HTMLResponse)
async def driver_brief_html(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> HTMLResponse:
    payload = await driver_brief(job_id, db, current_user)
    html = render_driver_brief_html(
        route=str(payload["route"]),
        fleet_name=str(payload["fleet_name"]),
        job_id=str(payload["job_id"]),
        brief=dict(payload["brief"] or {}),
        savings=payload.get("savings") if isinstance(payload.get("savings"), dict) else None,
        vehicle_id=payload.get("vehicle_id"),
    )
    return HTMLResponse(html)
