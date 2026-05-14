from __future__ import annotations

from api.services.driver_brief import build_driver_brief_from_job_result
from api.services.telemetry_csv import parse_telemetry_csv


def test_parse_telemetry_csv_flexible_headers():
    raw = "latitude,longitude,speed\n40.0,-105.0,55\n40.1,-105.1,60\n"
    rows, n = parse_telemetry_csv(raw)
    assert n == 2
    assert rows[0]["lat"] == 40.0
    assert rows[0]["lon"] == -105.0
    assert rows[0]["speed_kmh"] == 55.0


def test_driver_brief_merges_segments():
    result = {
        "optimized": {
            "total_distance_km": 10,
            "distances_m": [0, 1000, 2000],
            "speed_profile_ms": [20.0, 20.0, 25.0],
            "lat": [40.0, 40.01, 40.02],
            "lon": [-105.0, -105.01, -105.02],
        }
    }
    brief = build_driver_brief_from_job_result(result, speed_step_kmh=4.0)
    assert brief["segment_count"] >= 1
    assert len(brief["segments"]) >= 1
