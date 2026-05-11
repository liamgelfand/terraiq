"""Tests for /api/jobs — submit and poll job lifecycle."""
from __future__ import annotations

from httpx import AsyncClient


REGISTER_PAYLOAD = {
    "email": "fleet@test.dev",
    "full_name": "Fleet User",
    "password": "securepass",
    "fleet_name": "Test Fleet",
}

JOB_CONFIG = {
    "origin": "Denver, CO",
    "destination": "Grand Junction, CO",
    "vehicle_id": "freightliner_2022",
    "job_type": "optimize",
    "time_budget_fraction": 1.05,
}


async def _auth_headers(client: AsyncClient) -> dict:
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_submit_job_returns_pending(client: AsyncClient):
    headers = await _auth_headers(client)
    resp = await client.post("/api/jobs", json={"config": JOB_CONFIG}, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending"
    assert "id" in body


async def test_poll_job_returns_job(client: AsyncClient):
    headers = await _auth_headers(client)
    create_resp = await client.post("/api/jobs", json={"config": JOB_CONFIG}, headers=headers)
    job_id = create_resp.json()["id"]

    poll_resp = await client.get(f"/api/jobs/{job_id}", headers=headers)
    assert poll_resp.status_code == 200
    assert poll_resp.json()["id"] == job_id


async def test_jobs_list_scoped_to_fleet(client: AsyncClient):
    """Jobs submitted under one fleet are not visible to another fleet."""
    headers = await _auth_headers(client)
    await client.post("/api/jobs", json={"config": JOB_CONFIG}, headers=headers)

    # Register a second fleet
    other_payload = {**REGISTER_PAYLOAD, "email": "other@fleet.dev", "fleet_name": "Other Fleet"}
    await client.post("/auth/register", json=other_payload)
    other_token_resp = await client.post(
        "/auth/login",
        json={"email": other_payload["email"], "password": other_payload["password"]},
    )
    other_headers = {"Authorization": f"Bearer {other_token_resp.json()['access_token']}"}

    other_list = await client.get("/api/jobs", headers=other_headers)
    assert other_list.status_code == 200
    assert other_list.json() == []


async def test_unauthenticated_jobs_returns_401(client: AsyncClient):
    resp = await client.get("/api/jobs")
    assert resp.status_code == 401


async def test_submit_sweep_job(client: AsyncClient):
    headers = await _auth_headers(client)
    sweep_config = {**JOB_CONFIG, "job_type": "sweep"}
    resp = await client.post("/api/jobs", json={"config": sweep_config}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"
