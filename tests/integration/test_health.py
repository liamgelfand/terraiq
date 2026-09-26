"""Tests for the /health endpoint."""
from __future__ import annotations

from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_health_requires_no_auth(client: AsyncClient):
    """Health check must be publicly accessible — no token needed."""
    resp = await client.get("/health")
    assert resp.status_code == 200


async def test_ready_returns_ready(client: AsyncClient):
    resp = await client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert "version" in body
