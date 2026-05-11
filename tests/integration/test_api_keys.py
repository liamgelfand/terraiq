"""Tests for /api/keys — create, list, and revoke API keys."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

REGISTER = {
    "email": "keys@fleet.dev",
    "full_name": "Key User",
    "password": "securepass",
    "fleet_name": "Key Fleet",
}

OTHER_REGISTER = {
    "email": "other@fleet.dev",
    "full_name": "Other User",
    "password": "securepass",
    "fleet_name": "Other Fleet",
}


async def _auth_headers(client: AsyncClient, payload: dict = REGISTER) -> dict:
    await client.post("/auth/register", json=payload)
    resp = await client.post(
        "/auth/login", json={"email": payload["email"], "password": payload["password"]}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ── Create ────────────────────────────────────────────────────────────────────

async def test_create_key_returns_201(client: AsyncClient):
    headers = await _auth_headers(client)
    resp = await client.post("/api/keys", json={"name": "My Key"}, headers=headers)
    assert resp.status_code == 201


async def test_created_key_has_raw_key(client: AsyncClient):
    headers = await _auth_headers(client)
    resp = await client.post("/api/keys", json={"name": "Test Key"}, headers=headers)
    body = resp.json()
    assert "raw_key" in body
    assert body["raw_key"].startswith("tiq_")


async def test_created_key_has_prefix_not_full_secret(client: AsyncClient):
    """The list endpoint must never return the full key — only the prefix."""
    headers = await _auth_headers(client)
    create_resp = await client.post("/api/keys", json={"name": "K"}, headers=headers)
    raw_key = create_resp.json()["raw_key"]

    list_resp = await client.get("/api/keys", headers=headers)
    keys = list_resp.json()
    assert len(keys) == 1
    assert keys[0]["key_prefix"] != raw_key
    assert "raw_key" not in keys[0]


async def test_create_key_requires_auth(client: AsyncClient):
    resp = await client.post("/api/keys", json={"name": "K"})
    assert resp.status_code == 401


# ── List ──────────────────────────────────────────────────────────────────────

async def test_list_keys_empty_by_default(client: AsyncClient):
    headers = await _auth_headers(client)
    resp = await client.get("/api/keys", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_keys_returns_created_keys(client: AsyncClient):
    headers = await _auth_headers(client)
    await client.post("/api/keys", json={"name": "Key A"}, headers=headers)
    await client.post("/api/keys", json={"name": "Key B"}, headers=headers)
    resp = await client.get("/api/keys", headers=headers)
    assert len(resp.json()) == 2


async def test_keys_scoped_to_fleet(client: AsyncClient):
    """Fleet A's keys are invisible to Fleet B."""
    headers_a = await _auth_headers(client, REGISTER)
    await client.post("/api/keys", json={"name": "Fleet A Key"}, headers=headers_a)

    headers_b = await _auth_headers(client, OTHER_REGISTER)
    resp = await client.get("/api/keys", headers=headers_b)
    assert resp.json() == []


# ── Revoke ────────────────────────────────────────────────────────────────────

async def test_revoke_key_returns_204(client: AsyncClient):
    headers = await _auth_headers(client)
    key_id = (await client.post("/api/keys", json={"name": "K"}, headers=headers)).json()["id"]
    resp = await client.delete(f"/api/keys/{key_id}", headers=headers)
    assert resp.status_code == 204


async def test_revoke_nonexistent_key_returns_404(client: AsyncClient):
    headers = await _auth_headers(client)
    resp = await client.delete("/api/keys/nonexistent-id", headers=headers)
    assert resp.status_code == 404


async def test_revoke_another_fleets_key_returns_404(client: AsyncClient):
    """Users must not be able to revoke keys belonging to another fleet."""
    headers_a = await _auth_headers(client, REGISTER)
    key_id = (await client.post("/api/keys", json={"name": "K"}, headers=headers_a)).json()["id"]

    headers_b = await _auth_headers(client, OTHER_REGISTER)
    resp = await client.delete(f"/api/keys/{key_id}", headers=headers_b)
    assert resp.status_code == 404
