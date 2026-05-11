"""Tests for GET /api/vehicles."""
from __future__ import annotations

from httpx import AsyncClient


async def test_list_vehicles_returns_list(client: AsyncClient):
    resp = await client.get("/api/vehicles")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_list_vehicles_has_expected_fields(client: AsyncClient):
    resp = await client.get("/api/vehicles")
    for v in resp.json():
        assert "id" in v
        assert "name" in v
        assert "mass_kg" in v
        assert "max_speed_kmh" in v


async def test_list_vehicles_non_empty(client: AsyncClient):
    resp = await client.get("/api/vehicles")
    assert len(resp.json()) >= 1


async def test_list_vehicles_requires_no_auth(client: AsyncClient):
    """Vehicle list is a public, read-only endpoint."""
    resp = await client.get("/api/vehicles")
    assert resp.status_code == 200
