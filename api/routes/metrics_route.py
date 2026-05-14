from __future__ import annotations

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def metrics() -> Response:
    """Prometheus scrape endpoint (process metrics + any custom collectors)."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
