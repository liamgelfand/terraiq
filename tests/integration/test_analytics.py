"""Tests for GET /api/analytics."""
from __future__ import annotations

from datetime import datetime, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.fleet import Fleet
from api.models.job import Job
from api.models.user import User
from api.auth import hash_password

REGISTER = {
    "email": "analytics@fleet.dev",
    "full_name": "Analyst",
    "password": "securepass",
    "fleet_name": "Analytics Fleet",
}


async def _auth_headers(client: AsyncClient) -> dict:
    await client.post("/auth/register", json=REGISTER)
    resp = await client.post(
        "/auth/login", json={"email": REGISTER["email"], "password": REGISTER["password"]}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ── Auth guard ────────────────────────────────────────────────────────────────

async def test_analytics_requires_auth(client: AsyncClient):
    resp = await client.get("/api/analytics")
    assert resp.status_code == 401


# ── Empty fleet ───────────────────────────────────────────────────────────────

async def test_analytics_empty_fleet(client: AsyncClient):
    headers = await _auth_headers(client)
    resp = await client.get("/api/analytics", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_jobs"] == 0
    assert body["completed_jobs"] == 0
    assert body["total_fuel_saved_L"] == 0.0
    assert body["total_cost_saved_usd"] == 0.0


# ── With jobs ─────────────────────────────────────────────────────────────────

async def test_analytics_counts_pending_jobs(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_headers(client)

    # Fetch the fleet so we can insert jobs directly
    me = await client.get("/auth/me", headers=headers)
    fleet_id = me.json()["fleet_id"]

    job = Job(
        id="test-job-pending",
        fleet_id=fleet_id,
        status="pending",
        config={"origin": "A", "destination": "B"},
    )
    db_session.add(job)
    await db_session.commit()

    resp = await client.get("/api/analytics", headers=headers)
    body = resp.json()
    assert body["total_jobs"] == 1
    assert body["completed_jobs"] == 0


async def test_analytics_aggregates_completed_jobs(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_headers(client)
    me = await client.get("/auth/me", headers=headers)
    fleet_id = me.json()["fleet_id"]

    completed_result = {
        "savings": {
            "fuel_saved_liters": 12.5,
            "cost_saved_usd": 12.87,
            "co2_saved_kg": 33.5,
        },
        "optimized": {"total_distance_km": 250.0},
    }

    for i in range(2):
        job = Job(
            id=f"test-job-complete-{i}",
            fleet_id=fleet_id,
            status="completed",
            config={"origin": "A", "destination": "B"},
            result=completed_result,
            completed_at=datetime.now(timezone.utc),
        )
        db_session.add(job)
    await db_session.commit()

    resp = await client.get("/api/analytics", headers=headers)
    body = resp.json()
    assert body["completed_jobs"] == 2
    assert body["total_fuel_saved_L"] == pytest.approx(25.0, abs=0.01)
    assert body["total_cost_saved_usd"] == pytest.approx(25.74, abs=0.01)
    assert body["total_distance_km"] == pytest.approx(500.0, abs=0.01)


import pytest
