from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings


REGISTER = {
    "email": "quota@fleet.dev",
    "full_name": "Quota User",
    "password": "securepass",
    "fleet_name": "Quota Fleet",
}

JOB_CONFIG = {
    "origin": "Denver, CO",
    "destination": "Grand Junction, CO",
    "vehicle_id": "freightliner_2022",
    "job_type": "optimize",
    "time_budget_fraction": 1.05,
}


async def _headers(client: AsyncClient) -> dict[str, str]:
    await client.post("/auth/register", json=REGISTER)
    resp = await client.post(
        "/auth/login", json={"email": REGISTER["email"], "password": REGISTER["password"]}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def test_usage_includes_plan_fields(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "debug", False)
    headers = await _headers(client)
    resp = await client.get("/api/fleet/usage", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["billing_plan"] == "free"
    assert body["plan_label"] == "Trial"
    assert body["jobs_this_month"] == 0
    assert body["jobs_limit_monthly"] == settings.free_jobs_per_month
    assert body["jobs_remaining_this_month"] == settings.free_jobs_per_month


async def test_job_quota_returns_402(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "free_jobs_per_month", 1)
    headers = await _headers(client)
    first = await client.post("/api/jobs", json={"config": JOB_CONFIG}, headers=headers)
    assert first.status_code == 201
    second = await client.post("/api/jobs", json={"config": JOB_CONFIG}, headers=headers)
    assert second.status_code == 402
    detail = second.json()["detail"]
    assert detail["error_code"] == "QUOTA_EXCEEDED"


async def test_corridor_quota_returns_402(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "free_max_corridors", 2)
    headers = await _headers(client)
    # Register already seeds two starter corridors.
    resp = await client.post(
        "/api/corridors",
        json={
            "name": "Lane extra",
            "origin": "Denver, CO",
            "destination": "Boulder, CO",
        },
        headers=headers,
    )
    assert resp.status_code == 402
    assert resp.json()["detail"]["error_code"] == "CORRIDOR_LIMIT"


async def test_debug_usage_has_no_job_limit(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "debug", True)
    headers = await _headers(client)
    resp = await client.get("/api/fleet/usage", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["jobs_limit_monthly"] is None
    assert body["jobs_remaining_this_month"] is None
    assert body["plan_label"] == "Dev"


async def test_paid_plan_skips_job_quota(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "free_jobs_per_month", 1)
    headers = await _headers(client)
    me = await client.get("/auth/me", headers=headers)
    fleet_id = me.json()["fleet_id"]

    from api.models.fleet import Fleet  # noqa: PLC0415

    fleet = await db_session.get(Fleet, fleet_id)
    assert fleet is not None
    fleet.billing_plan = "pilot"
    await db_session.commit()

    first = await client.post("/api/jobs", json={"config": JOB_CONFIG}, headers=headers)
    second = await client.post("/api/jobs", json={"config": JOB_CONFIG}, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201
