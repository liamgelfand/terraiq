from __future__ import annotations

from httpx import AsyncClient


async def test_public_meta(client: AsyncClient):
    resp = await client.get("/api/public/meta")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "TerraIQ"
    assert "version" in body
    assert body["pilot_available"] is True


async def test_demo_request_accepted(client: AsyncClient):
    resp = await client.post(
        "/api/public/demo-request",
        json={
            "name": "Alex Dispatcher",
            "email": "alex@fleet.example",
            "company": "Example Haul",
            "fleet_size": "40",
            "message": "I-70 Denver to Grand Junction",
        },
    )
    assert resp.status_code == 202
    assert resp.json()["ok"] is True


async def test_demo_request_validates_email(client: AsyncClient):
    resp = await client.post(
        "/api/public/demo-request",
        json={"name": "A", "email": "not-an-email", "company": "X"},
    )
    assert resp.status_code == 422
