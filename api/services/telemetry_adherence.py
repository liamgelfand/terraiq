from __future__ import annotations

import math
from typing import Any


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _nearest_route_index(
    lat: list[float], lon: list[float], plat: float, plon: float
) -> int:
    best_i = 0
    best_d = float("inf")
    for i, (la, lo) in enumerate(zip(rlat, rlon)):
        d = _haversine_m(plat, plon, float(la), float(lo))
        if d < best_d:
            best_d = d
            best_i = i
    return best_i


def compute_adherence(
    job_result: dict[str, Any],
    points: list[dict[str, Any]],
    *,
    tolerance_kmh: float = 12.0,
) -> dict[str, Any]:
    """
    Map each telemetry sample to the nearest vertex on the optimized route polyline
    and compare speed to the recommended profile (m/s stored → km/h).
    """
    opt = job_result.get("optimized") or {}
    rlat = opt.get("lat") or []
    rlon = opt.get("lon") or []
    speeds_ms = opt.get("speed_profile_ms") or []
    if len(rlat) < 2 or len(rlon) < 2 or not speeds_ms:
        return {
            "error": "job_result_missing_polyline",
            "points_total": len(points),
            "points_in_band": 0,
            "pct_in_band": None,
        }

    in_band = 0
    details: list[dict[str, Any]] = []
    for p in points:
        try:
            plat = float(p["lat"])
            plon = float(p["lon"])
            spd = float(p.get("speed_kmh", p.get("speed", 0)))
        except (KeyError, TypeError, ValueError):
            continue
        idx = _nearest_route_index([float(x) for x in rlat], [float(x) for x in rlon], plat, plon)
        rec_kmh = float(speeds_ms[idx]) * 3.6 if idx < len(speeds_ms) else 0.0
        ok = abs(spd - rec_kmh) <= tolerance_kmh
        if ok:
            in_band += 1
        if len(details) < 50:
            details.append({
                "lat": plat,
                "lon": plon,
                "speed_kmh": round(spd, 2),
                "recommended_kmh": round(rec_kmh, 2),
                "in_band": ok,
            })

    total = len(points)
    pct = round(100.0 * in_band / total, 2) if total else None
    return {
        "points_total": total,
        "points_in_band": in_band,
        "pct_in_band": pct,
        "tolerance_kmh": tolerance_kmh,
        "sample_points": details,
    }
