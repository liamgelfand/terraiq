"""
Tests for the public /v1/optimize endpoint (API key authentication).

Celery dispatch is stubbed in conftest so no workers run during tests.
"""
from __future__ import annotations

import hashlib

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.api_key import ApiKey
from api.models.fleet import Fleet

REGISTER = {
    "email": "v1@fleet.dev",
    "full_name": "API User",
    "password": "securepass",
    "fleet_name": "V1 Fleet",
}

VALID_BODY = {
    "origin": "Denver, CO",
    "destination": "Grand Junction, CO",
}


async def _create_api_key(client: AsyncClient, db_session: AsyncSession) -> str:
    """Register a user, create an API key via the internal endpoint, return the raw key."""
    await client.post("/auth/register", json=REGISTER)
    token_resp = await client.post(
        "/auth/login", json={"email": REGISTER["email"], "password": REGISTER["password"]}
    )
    headers = {"Authorization": f"Bearer {token_resp.json()['access_token']}"}
    key_resp = await client.post("/api/keys", json={"name": "Test Key"}, headers=headers)
    return key_resp.json()["raw_key"]


# ── Auth guard ────────────────────────────────────────────────────────────────

async def test_submit_without_api_key_returns_422_or_401(client: AsyncClient):
    resp = await client.post("/v1/optimize", json=VALID_BODY)
    assert resp.status_code in (401, 422)


async def test_submit_with_bad_api_key_returns_401(client: AsyncClient):
    resp = await client.post(
        "/v1/optimize", json=VALID_BODY, headers={"X-API-Key": "tiq_fakefakefake"}
    )
    assert resp.status_code == 401


# ── Submission ────────────────────────────────────────────────────────────────

async def test_submit_valid_request_returns_202(client: AsyncClient, db_session: AsyncSession):
    raw_key = await _create_api_key(client, db_session)
    resp = await client.post(
        "/v1/optimize", json=VALID_BODY, headers={"X-API-Key": raw_key}
    )
    assert resp.status_code == 202


async def test_submit_returns_job_id_and_poll_url(client: AsyncClient, db_session: AsyncSession):
    raw_key = await _create_api_key(client, db_session)
    resp = await client.post(
        "/v1/optimize", json=VALID_BODY, headers={"X-API-Key": raw_key}
    )
    body = resp.json()
    assert "job_id" in body
    assert "poll_url" in body
    assert body["status"] == "pending"


async def test_submit_with_load_kg(client: AsyncClient, db_session: AsyncSession):
    raw_key = await _create_api_key(client, db_session)
    body_with_load = {**VALID_BODY, "vehicle": {"load_kg": 5000}}
    resp = await client.post(
        "/v1/optimize", json=body_with_load, headers={"X-API-Key": raw_key}
    )
    assert resp.status_code == 202


async def test_submit_with_simplified_flag(client: AsyncClient, db_session: AsyncSession):
    raw_key = await _create_api_key(client, db_session)
    resp = await client.post(
        "/v1/optimize",
        json={**VALID_BODY, "simplified": True},
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 202


async def test_submit_increments_key_usage(client: AsyncClient, db_session: AsyncSession):
    raw_key = await _create_api_key(client, db_session)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    from sqlalchemy import select  # noqa: PLC0415
    from api.models.api_key import ApiKey  # noqa: PLC0415

    before = (
        await db_session.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    ).scalar_one().usage_count

    await client.post("/v1/optimize", json=VALID_BODY, headers={"X-API-Key": raw_key})
    await db_session.refresh(
        (await db_session.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))).scalar_one()
    )
    after = (
        await db_session.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    ).scalar_one().usage_count

    assert after == before + 1


# ── Polling ───────────────────────────────────────────────────────────────────

async def test_poll_returns_job_by_id(client: AsyncClient, db_session: AsyncSession):
    raw_key = await _create_api_key(client, db_session)
    job_id = (
        await client.post("/v1/optimize", json=VALID_BODY, headers={"X-API-Key": raw_key})
    ).json()["job_id"]

    poll = await client.get(f"/v1/optimize/{job_id}", headers={"X-API-Key": raw_key})
    assert poll.status_code == 200
    assert poll.json()["job_id"] == job_id


async def test_poll_unknown_job_returns_404(client: AsyncClient, db_session: AsyncSession):
    raw_key = await _create_api_key(client, db_session)
    resp = await client.get("/v1/optimize/no-such-job", headers={"X-API-Key": raw_key})
    assert resp.status_code == 404


# ── Validation ────────────────────────────────────────────────────────────────

async def test_time_budget_below_1_rejected(client: AsyncClient, db_session: AsyncSession):
    raw_key = await _create_api_key(client, db_session)
    resp = await client.post(
        "/v1/optimize",
        json={**VALID_BODY, "time_budget_fraction": 0.5},
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 422


async def test_load_kg_above_max_rejected(client: AsyncClient, db_session: AsyncSession):
    raw_key = await _create_api_key(client, db_session)
    resp = await client.post(
        "/v1/optimize",
        json={**VALID_BODY, "vehicle": {"load_kg": 99_999}},
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 422
