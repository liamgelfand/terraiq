from __future__ import annotations

from httpx import AsyncClient

from api.config import settings


async def test_demo_request_is_persisted(client: AsyncClient):
    resp = await client.post(
        "/api/public/demo-request",
        json={
            "name": "Casey Dispatcher",
            "email": "casey@haul.example",
            "company": "Haul Co",
            "fleet_size": "25",
            "message": "I-70",
        },
    )
    assert resp.status_code == 202
    assert resp.json()["ok"] is True
    assert resp.json()["lead_id"]


async def test_leads_require_founder(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={
            "email": "normal@fleet.dev",
            "full_name": "Norm",
            "password": "securepass",
            "fleet_name": "Norm Fleet",
        },
    )
    login = await client.post(
        "/auth/login", json={"email": "normal@fleet.dev", "password": "securepass"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    resp = await client.get("/api/leads", headers=headers)
    assert resp.status_code == 403


async def test_founder_lists_leads(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "founding_admin_email", "founder@terraiq.dev")
    await client.post(
        "/auth/register",
        json={
            "email": "founder@terraiq.dev",
            "full_name": "Founder",
            "password": "securepass",
            "fleet_name": "TerraIQ",
        },
    )
    await client.post(
        "/api/public/demo-request",
        json={"name": "Pat", "email": "pat@x.com", "company": "X Haul"},
    )
    login = await client.post(
        "/auth/login", json={"email": "founder@terraiq.dev", "password": "securepass"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = await client.get("/auth/me", headers=headers)
    assert me.json()["is_founder"] is True
    listed = await client.get("/api/leads", headers=headers)
    assert listed.status_code == 200
    assert any(row["company"] == "X Haul" for row in listed.json())


async def test_register_seeds_starter_corridors(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={
            "email": "seed@fleet.dev",
            "full_name": "Seed",
            "password": "securepass",
            "fleet_name": "Seed Fleet",
        },
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    corridors = await client.get("/api/corridors", headers=headers)
    assert corridors.status_code == 200
    assert len(corridors.json()) == 2
    status = await client.get("/api/fleet/onboarding-status", headers=headers)
    assert status.status_code == 200
    assert status.json()["starter_seeded"] is True
    report = await client.get("/api/analytics/report.html", headers=headers)
    assert report.status_code == 200
    assert "savings report" in report.text.lower()
