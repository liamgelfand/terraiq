from __future__ import annotations

from typing import Any


def build_driver_brief_from_job_result(result: dict[str, Any], *, speed_step_kmh: float = 5.0) -> dict[str, Any]:
    """
    Merge consecutive route samples into short coaching segments from the optimized profile.
    Uses optimized lat/lon/distances_m and speed_profile_ms (m/s → km/h).
    """
    opt = result.get("optimized") or {}
    dist_m = opt.get("distances_m") or []
    speeds_ms = opt.get("speed_profile_ms") or []
    lat = opt.get("lat") or []
    lon = opt.get("lon") or []
    if not dist_m or not speeds_ms or len(dist_m) != len(speeds_ms):
        return {"segments": [], "distance_km": opt.get("total_distance_km")}

    segments: list[dict[str, Any]] = []
    n = len(speeds_ms)
    i_start = 0

    def emit_segment(i_end: int) -> None:
        d_start_km = float(dist_m[i_start]) / 1000.0
        d_end_km = float(dist_m[i_end]) / 1000.0
        tgt = round(float(speeds_ms[i_start]) * 3.6, 1)
        la_s = float(lat[i_start]) if i_start < len(lat) else None
        lo_s = float(lon[i_start]) if i_start < len(lon) else None
        la_e = float(lat[i_end]) if i_end < len(lat) else None
        lo_e = float(lon[i_end]) if i_end < len(lon) else None
        mph = round(tgt / 1.60934, 0)
        segments.append({
            "start_km": round(d_start_km, 2),
            "end_km": round(d_end_km, 2),
            "target_speed_kmh": tgt,
            "target_speed_mph": mph,
            "summary": (
                f"Hold ~{tgt:.0f} km/h ({mph:.0f} mph) from {d_start_km:.1f}–{d_end_km:.1f} km"
            ),
            "start_lat": la_s,
            "start_lon": lo_s,
            "end_lat": la_e,
            "end_lon": lo_e,
        })

    for i in range(1, n):
        prev_kmh = float(speeds_ms[i - 1]) * 3.6
        cur_kmh = float(speeds_ms[i]) * 3.6
        if abs(cur_kmh - prev_kmh) >= speed_step_kmh:
            emit_segment(i - 1)
            i_start = i
    emit_segment(n - 1)

    return {
        "segments": segments[:200],
        "distance_km": opt.get("total_distance_km"),
        "segment_count": len(segments),
    }


def render_driver_brief_html(
    *,
    route: str,
    fleet_name: str,
    job_id: str,
    brief: dict[str, Any],
    savings: dict[str, Any] | None = None,
    vehicle_id: str | None = None,
) -> str:
    """Print-friendly HTML a dispatcher can hand to a driver (browser File → Print)."""
    rows = []
    for i, seg in enumerate(brief.get("segments") or [], start=1):
        rows.append(
            "<tr>"
            f"<td>{i}</td>"
            f"<td>{seg.get('start_km', '')}–{seg.get('end_km', '')}</td>"
            f"<td>{seg.get('target_speed_mph', '')}</td>"
            f"<td>{seg.get('target_speed_kmh', '')}</td>"
            f"<td>{seg.get('summary', '')}</td>"
            "</tr>"
        )
    body_rows = "\n".join(rows) or "<tr><td colspan='5'>No speed segments for this job.</td></tr>"
    fuel = ""
    if savings:
        pct = savings.get("fuel_saved_pct")
        liters = savings.get("fuel_saved_liters")
        usd = savings.get("cost_saved_usd")
        fuel = (
            f"<p class='meta'>Simulated vs baseline: "
            f"{liters if liters is not None else '-'} L "
            f"({pct if pct is not None else '-'}%) · "
            f"${usd if usd is not None else '-'}.</p>"
            "<p class='note'>Simulated savings assume the speed profile is followed. "
            "Measure fuel on the truck before treating this as a guarantee.</p>"
        )
    dist = brief.get("distance_km")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Driver brief - {route}</title>
  <style>
    body {{ font-family: Georgia, 'Times New Roman', serif; color: #1c1917; margin: 24px; }}
    h1 {{ font-size: 22px; margin: 0 0 4px; }}
    .sub {{ color: #57534e; margin: 0 0 16px; font-size: 14px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
    th, td {{ border: 1px solid #d6d3d1; padding: 8px 10px; text-align: left; }}
    th {{ background: #f5f5f4; }}
    .meta {{ font-size: 14px; }}
    .note {{ font-size: 12px; color: #78716c; }}
    @media print {{
      body {{ margin: 12px; }}
      button {{ display: none; }}
    }}
  </style>
</head>
<body>
  <button onclick="window.print()">Print</button>
  <h1>TerraIQ driver brief</h1>
  <p class="sub">{fleet_name} · {route}<br/>
  Job {job_id[:8]}… · {dist if dist is not None else '-'} km
  {f' · {vehicle_id}' if vehicle_id else ''}</p>
  {fuel}
  <table>
    <thead>
      <tr><th>#</th><th>Miles / km along route</th><th>mph</th><th>km/h</th><th>Coaching</th></tr>
    </thead>
    <tbody>
      {body_rows}
    </tbody>
  </table>
</body>
</html>"""

