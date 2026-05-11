"""
Unit tests for api/auth.py — password hashing and JWT utilities.

No database, no HTTP, no external services.
"""
from __future__ import annotations

import time

import pytest
from jose import JWTError

from api.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# ── Password hashing ──────────────────────────────────────────────────────────

def test_hash_password_returns_non_empty_string():
    h = hash_password("mysecretpassword")
    assert isinstance(h, str)
    assert len(h) > 0


def test_hash_is_not_plaintext():
    plain = "mysecretpassword"
    assert hash_password(plain) != plain


def test_same_password_produces_different_hashes():
    """bcrypt embeds a random salt — two hashes of the same input must differ."""
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2


def test_verify_correct_password_returns_true():
    plain = "correct-horse-battery-staple"
    assert verify_password(plain, hash_password(plain)) is True


def test_verify_wrong_password_returns_false():
    hashed = hash_password("real-password")
    assert verify_password("wrong-password", hashed) is False


def test_verify_empty_password_returns_false():
    hashed = hash_password("has-content")
    assert verify_password("", hashed) is False


def test_verify_rejects_plaintext_as_hash():
    """Passing a plaintext string as the hash arg should not crash or return True."""
    assert verify_password("anypassword", "notahash") is False


# ── JWT creation & decoding ───────────────────────────────────────────────────

def test_create_access_token_returns_string():
    token = create_access_token("user-123", "fleet-456")
    assert isinstance(token, str)
    assert len(token.split(".")) == 3  # header.payload.signature


def test_decode_returns_correct_claims():
    token = create_access_token("user-abc", "fleet-xyz")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-abc"
    assert payload["fleet_id"] == "fleet-xyz"


def test_token_includes_expiry():
    token = create_access_token("u", "f")
    payload = decode_access_token(token)
    assert "exp" in payload
    assert payload["exp"] > time.time()


def test_tampered_token_raises_jwt_error():
    token = create_access_token("u", "f")
    # Flip the last character to corrupt the signature
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(JWTError):
        decode_access_token(tampered)


def test_completely_fake_token_raises_jwt_error():
    with pytest.raises(JWTError):
        decode_access_token("not.a.jwt")


def test_different_users_get_different_tokens():
    t1 = create_access_token("user-1", "fleet-1")
    t2 = create_access_token("user-2", "fleet-1")
    assert t1 != t2
