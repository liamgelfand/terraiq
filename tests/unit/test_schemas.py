"""
Unit tests for Pydantic schemas — validation rules, defaults, and edge cases.

No I/O, no database.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from api.schemas.job import JobConfig, JobCreate


# ── RegisterRequest ───────────────────────────────────────────────────────────

VALID_REGISTER = {
    "email": "user@fleet.com",
    "full_name": "Jane Doe",
    "password": "securepass",
    "fleet_name": "Acme Fleet",
}


def test_register_valid():
    r = RegisterRequest(**VALID_REGISTER)
    assert r.email == "user@fleet.com"


def test_register_invalid_email_raises():
    with pytest.raises(ValidationError):
        RegisterRequest(**{**VALID_REGISTER, "email": "not-an-email"})


def test_register_short_password_raises():
    with pytest.raises(ValidationError):
        RegisterRequest(**{**VALID_REGISTER, "password": "short"})


def test_register_empty_full_name_raises():
    with pytest.raises(ValidationError):
        RegisterRequest(**{**VALID_REGISTER, "full_name": ""})


def test_register_empty_fleet_name_raises():
    with pytest.raises(ValidationError):
        RegisterRequest(**{**VALID_REGISTER, "fleet_name": ""})


def test_register_email_domain_normalised_to_lowercase():
    """email-validator lowercases the domain but preserves the local part case."""
    r = RegisterRequest(**{**VALID_REGISTER, "email": "User@FLEET.COM"})
    assert r.email == "User@fleet.com"


# ── LoginRequest ──────────────────────────────────────────────────────────────

def test_login_valid():
    r = LoginRequest(email="a@b.com", password="any")
    assert r.email == "a@b.com"


def test_login_invalid_email_raises():
    with pytest.raises(ValidationError):
        LoginRequest(email="bad", password="pass")


# ── ResetPasswordRequest ──────────────────────────────────────────────────────

def test_reset_valid():
    r = ResetPasswordRequest(token="sometoken", new_password="longenough")
    assert r.token == "sometoken"


def test_reset_short_password_raises():
    with pytest.raises(ValidationError):
        ResetPasswordRequest(token="t", new_password="short")


# ── ForgotPasswordRequest ─────────────────────────────────────────────────────

def test_forgot_valid():
    ForgotPasswordRequest(email="a@b.com")


def test_forgot_invalid_email_raises():
    with pytest.raises(ValidationError):
        ForgotPasswordRequest(email="bad")


# ── JobConfig ─────────────────────────────────────────────────────────────────

VALID_JOB = {"origin": "Denver, CO", "destination": "Grand Junction, CO"}


def test_job_config_defaults():
    c = JobConfig(**VALID_JOB)
    assert c.vehicle_id == "freightliner_2022"
    assert c.job_type == "optimize"
    assert c.time_budget_fraction == pytest.approx(1.05)
    assert c.load_kg is None


def test_job_config_time_budget_below_1_raises():
    with pytest.raises(ValidationError):
        JobConfig(**{**VALID_JOB, "time_budget_fraction": 0.9})


def test_job_config_time_budget_above_2_raises():
    with pytest.raises(ValidationError):
        JobConfig(**{**VALID_JOB, "time_budget_fraction": 2.1})


def test_job_config_load_kg_negative_raises():
    with pytest.raises(ValidationError):
        JobConfig(**{**VALID_JOB, "load_kg": -100})


def test_job_config_load_kg_above_max_raises():
    with pytest.raises(ValidationError):
        JobConfig(**{**VALID_JOB, "load_kg": 18_000})


def test_job_config_load_kg_zero_is_valid():
    c = JobConfig(**{**VALID_JOB, "load_kg": 0})
    assert c.load_kg == 0.0


def test_job_config_load_kg_max_is_valid():
    c = JobConfig(**{**VALID_JOB, "load_kg": 17_000})
    assert c.load_kg == 17_000.0


def test_job_config_missing_origin_raises():
    with pytest.raises(ValidationError):
        JobConfig(destination="Denver, CO")


def test_job_config_missing_destination_raises():
    with pytest.raises(ValidationError):
        JobConfig(origin="Denver, CO")


def test_job_create_wraps_config():
    jc = JobCreate(config=JobConfig(**VALID_JOB))
    assert jc.config.origin == "Denver, CO"
