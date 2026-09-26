from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from api.deps import get_current_user, get_db
from api.models.job import Job

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


async def _fleet_analytics(db: AsyncSession, fleet_id: str) -> dict:
    result = await db.execute(
        select(Job).where(Job.fleet_id == fleet_id, Job.status == "completed")
    )
    completed_jobs = list(result.scalars().all())

    total_result = await db.execute(
        select(func.count()).select_from(Job).where(Job.fleet_id == fleet_id)
    )
    total_jobs = total_result.scalar() or 0

    fuel_saved_L = 0.0
    cost_saved_usd = 0.0
    co2_saved_kg = 0.0
    distance_km = 0.0
    rows: list[dict] = []

    for job in completed_jobs:
        if not job.result:
            continue
        savings = job.result.get("savings", {}) or {}
        fuel_saved_L += savings.get("fuel_saved_liters", 0) or 0
        cost_saved_usd += savings.get("cost_saved_usd", 0) or 0
        co2_saved_kg += savings.get("co2_saved_kg", 0) or 0
        opt = job.result.get("optimized", {}) or {}
        distance_km += opt.get("total_distance_km", 0) or 0
        cfg = job.config or {}
        rows.append(
            {
                "route": f"{cfg.get('origin', '')} → {cfg.get('destination', '')}",
                "fuel_L": savings.get("fuel_saved_liters"),
                "pct": savings.get("fuel_saved_pct"),
                "usd": savings.get("cost_saved_usd"),
            }
        )

    return {
        "total_jobs": total_jobs,
        "completed_jobs": len(completed_jobs),
        "total_fuel_saved_L": round(fuel_saved_L, 2),
        "total_cost_saved_usd": round(cost_saved_usd, 2),
        "total_co2_saved_kg": round(co2_saved_kg, 2),
        "total_distance_km": round(distance_km, 2),
        "rows": rows,
    }


@router.get("")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    _user, fleet = current_user
    data = await _fleet_analytics(db, fleet.id)
    data.pop("rows", None)
    return data


@router.get("/report.html", response_class=HTMLResponse)
async def analytics_report_html(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> HTMLResponse:
    """Printable case-study pack for a pilot conversation."""
    _user, fleet = current_user
    data = await _fleet_analytics(db, fleet.id)
    body_rows = "".join(
        (
            "<tr>"
            f"<td>{r['route']}</td>"
            f"<td>{r['fuel_L'] if r['fuel_L'] is not None else '-'}</td>"
            f"<td>{r['pct'] if r['pct'] is not None else '-'}</td>"
            f"<td>{r['usd'] if r['usd'] is not None else '-'}</td>"
            "</tr>"
        )
        for r in data["rows"][:50]
    ) or "<tr><td colspan='4'>No completed jobs yet.</td></tr>"
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<title>TerraIQ savings report - {fleet.name}</title>
<style>
  body {{ font-family: Georgia, serif; margin: 28px; color: #1c1917; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  th, td {{ border: 1px solid #d6d3d1; padding: 8px; text-align: left; }}
  th {{ background: #f5f5f4; }}
  .note {{ font-size: 12px; color: #78716c; }}
  @media print {{ button {{ display: none; }} }}
</style></head><body>
<button onclick="window.print()">Print</button>
<h1>TerraIQ savings report</h1>
<p>{fleet.name}</p>
<p>Completed jobs: {data['completed_jobs']} / {data['total_jobs']} ·
Simulated fuel: {data['total_fuel_saved_L']} L ·
${data['total_cost_saved_usd']} ·
{data['total_co2_saved_kg']} kg CO₂ ·
{data['total_distance_km']} km</p>
<p class="note">These totals are simulated vs the model baseline. They are not a fuel guarantee.
Use adherence + pump/ELD fuel before you quote a customer percentage.</p>
<table>
<thead><tr><th>Route</th><th>Fuel saved (L)</th><th>%</th><th>Cost ($)</th></tr></thead>
<tbody>{body_rows}</tbody>
</table>
</body></html>"""
    return HTMLResponse(html)
