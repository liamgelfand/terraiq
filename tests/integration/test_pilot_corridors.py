"""Pilot features: saved corridors and batches API surface."""
from __future__ import annotations

from httpx import AsyncClient

REGISTER_PAYLOAD = {
    "email": "pilot@test.dev",
    "full_name": "Pilot User",
    "password": "securepass",
    "fleet_name": "Pilot Fleet",
}


async def _headers(client: AsyncClient) -> dict[str, str]:
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_corridor_crud_and_batch(client: AsyncClient):
    headers = await _headers(client)
    cresp = await client.post(
        "/api/corridors",
        headers=headers,
        json={
            "name": "Denver–GJ",
            "origin": "Denver, CO",
            "destination": "Grand Junction, CO",
            "vehicle_id": "freightliner_2022",
            "time_budget_fraction": 1.05,
        },
    )
    assert cresp.status_code == 201
    cid = cresp.json()["id"]

    bresp = await client.post(
        "/api/batches",
        headers=headers,
        json={"corridor_ids": [cid], "name": "week-1"},
    )
    assert bresp.status_code == 201
    assert bresp.json()["status"] in ("pending", "running", "completed", "failed")

    ops = await client.get("/api/pilot/ops-board", headers=headers)
    assert ops.status_code == 200
    rows = ops.json()
    assert len(rows) == 1
    assert rows[0]["corridor_id"] == cid


async def test_data_export_admin(client: AsyncClient):
    headers = await _headers(client)
    resp = await client.get("/api/fleet/data-export", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "corridors" in body
    assert body["fleet_name"] == "Pilot Fleet"


async def test_job_create_with_corridor(client: AsyncClient):
    headers = await _headers(client)
    cresp = await client.post(
        "/api/corridors",
        headers=headers,
        json={
            "name": "Route A",
            "origin": "Denver, CO",
            "destination": "Boulder, CO",
        },
    )
    assert cresp.status_code == 201
    cid = cresp.json()["id"]

    jresp = await client.post(
        "/api/jobs",
        headers=headers,
        json={
            "corridor_id": cid,
            "config": {
                "origin": "Denver, CO",
                "destination": "Boulder, CO",
                "vehicle_id": "freightliner_2022",
                "job_type": "optimize",
                "time_budget_fraction": 1.05,
            },
        },
    )
    assert jresp.status_code == 201
    assert jresp.json()["corridor_id"] == cid
