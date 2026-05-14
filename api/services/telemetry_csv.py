from __future__ import annotations

import csv
import io
from typing import Any


_MAX_ROWS = 50_000

_HEADER_ALIASES = {
    "timestamp": "ts",
    "time": "ts",
    "ts": "ts",
    "lat": "lat",
    "latitude": "lat",
    "lon": "lon",
    "lng": "lon",
    "longitude": "lon",
    "speed_kmh": "speed_kmh",
    "speed": "speed_kmh",
    "speedkph": "speed_kmh",
    "velocity_kmh": "speed_kmh",
}


def _normalize_header(h: str) -> str | None:
    key = (h or "").strip().lower().replace(" ", "_")
    return _HEADER_ALIASES.get(key)


def parse_telemetry_csv(raw: str) -> tuple[list[dict[str, Any]], int]:
    """
    Parse CSV with flexible headers. Required: lat, lon; optional: timestamp, speed_kmh.
    """
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames:
        raise ValueError("empty_csv")

    rows: list[dict[str, Any]] = []
    for row in reader:
        out: dict[str, Any] = {}
        for k, v in row.items():
            alias = _normalize_header(k or "")
            if not alias or v is None or str(v).strip() == "":
                continue
            if alias == "ts":
                out["timestamp"] = str(v).strip()
            elif alias == "lat":
                out["lat"] = float(v)
            elif alias == "lon":
                out["lon"] = float(v)
            elif alias == "speed_kmh":
                out["speed_kmh"] = float(v)
        if "lat" in out and "lon" in out:
            if "speed_kmh" not in out:
                out["speed_kmh"] = 0.0
            rows.append(out)
        if len(rows) >= _MAX_ROWS:
            break

    if len(rows) < 2:
        raise ValueError("need_at_least_two_valid_rows")

    return rows, len(rows)
