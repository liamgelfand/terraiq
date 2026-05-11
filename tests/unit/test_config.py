"""
Unit tests for api/config.py — settings loading and secret validation.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.config import Settings, _DEFAULT_JWT_SECRET


def test_default_settings_load():
    s = Settings()
    assert s.debug is True  # local dev default
    assert s.jwt_algorithm == "HS256"
    assert s.jwt_expire_days == 30


def test_debug_true_allows_default_secret():
    """In debug mode the default JWT secret is acceptable."""
    s = Settings(debug=True, jwt_secret=_DEFAULT_JWT_SECRET)
    assert s.jwt_secret == _DEFAULT_JWT_SECRET


def test_debug_false_with_default_secret_raises():
    """Production mode must refuse to start with the default secret."""
    with pytest.raises((ValidationError, ValueError)):
        Settings(debug=False, jwt_secret=_DEFAULT_JWT_SECRET)


def test_debug_false_with_custom_secret_passes():
    s = Settings(debug=False, jwt_secret="a-very-long-custom-secret-for-production")
    assert s.jwt_secret == "a-very-long-custom-secret-for-production"


def test_jwt_expire_days_can_be_overridden():
    s = Settings(jwt_expire_days=7)
    assert s.jwt_expire_days == 7
