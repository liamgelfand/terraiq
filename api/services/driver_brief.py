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
        segments.append({
            "start_km": round(d_start_km, 2),
            "end_km": round(d_end_km, 2),
            "target_speed_kmh": tgt,
            "summary": (
                f"Hold ~{tgt:.0f} km/h from {d_start_km:.1f}–{d_end_km:.1f} km along route"
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
