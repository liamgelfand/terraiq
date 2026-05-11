"""Tests for /auth/* endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


REGISTER_PAYLOAD = {
    "email": "test@fleet.dev",
    "full_name": "Test User",
    "password": "securepass",
    "fleet_name": "Test Fleet",
}


async def _register_and_login(client: AsyncClient) -> str:
    """Helper: register a user and return a valid JWT."""
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    return resp.json()["access_token"]


# ── Registration ───────────────────────────────────────────────────────────────

async def test_register_creates_user(client: AsyncClient):
    resp = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    # Register returns a JWT; confirm the user exists by hitting /auth/me
    assert "access_token" in body
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == REGISTER_PAYLOAD["email"]


async def test_register_duplicate_email_returns_409(client: AsyncClient):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 409
    assert "already" in resp.json()["detail"].lower()


async def test_register_short_password_rejected(client: AsyncClient):
    payload = {**REGISTER_PAYLOAD, "password": "short"}
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 422


async def test_register_invalid_email_rejected(client: AsyncClient):
    payload = {**REGISTER_PAYLOAD, "email": "not-an-email"}
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 422


# ── Login ──────────────────────────────────────────────────────────────────────

async def test_login_returns_token(client: AsyncClient):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password_returns_401(client: AsyncClient):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email_returns_401(client: AsyncClient):
    resp = await client.post(
        "/auth/login",
        json={"email": "nobody@fleet.dev", "password": "anypassword"},
    )
    assert resp.status_code == 401


# ── /auth/me ───────────────────────────────────────────────────────────────────

async def test_me_returns_user_info(client: AsyncClient):
    token = await _register_and_login(client)
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == REGISTER_PAYLOAD["email"]
    assert body["fleet_name"] == REGISTER_PAYLOAD["fleet_name"]


async def test_me_without_token_returns_401(client: AsyncClient):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_with_invalid_token_returns_401(client: AsyncClient):
    resp = await client.get("/auth/me", headers={"Authorization": "Bearer bogus.token.here"})
    assert resp.status_code == 401


# ── Password reset ─────────────────────────────────────────────────────────────

async def test_forgot_password_always_200(client: AsyncClient):
    """The endpoint never reveals whether the email exists."""
    resp = await client.post("/auth/forgot-password", json={"email": "nobody@fleet.dev"})
    assert resp.status_code == 200


async def test_reset_password_invalid_token_returns_400(client: AsyncClient):
    resp = await client.post(
        "/auth/reset-password",
        json={"token": "completely-fake-token", "new_password": "newpassword123"},
    )
    assert resp.status_code == 400
