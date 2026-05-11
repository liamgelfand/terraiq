from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import create_access_token, hash_password, verify_password
from api.deps import get_current_user, get_db
from api.models.fleet import Fleet
from api.models.password_reset import PasswordResetToken
from api.models.user import User
from api.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> dict:
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    fleet = Fleet(name=body.fleet_name)
    db.add(fleet)
    await db.flush()  # populate fleet.id before using it

    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        fleet_id=fleet.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.fleet_id)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id, user.fleet_id)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: tuple[User, Fleet] = Depends(get_current_user),
) -> dict:
    user, fleet = current_user
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "fleet_id": user.fleet_id,
        "fleet_name": fleet.name,
    }


@router.post("/forgot-password", status_code=200)
async def forgot_password(
    body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Always returns 200 so the response does not reveal whether the email exists.
    The reset link is logged to the server console (replace with email send in production).
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        reset_token = PasswordResetToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(reset_token)
        await db.commit()

        # In production: send an email with this link.
        # For now, the link is printed to the uvicorn console so you can use it locally.
        reset_url = f"http://localhost:5173/?reset_token={raw_token}"
        logger.warning(
            "\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            " PASSWORD RESET REQUESTED\n"
            f" User  : {user.email}\n"
            f" Link  : {reset_url}\n"
            " Expires in 1 hour.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=200)
async def reset_password(
    body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> dict:
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > now,
        )
    )
    reset_token = result.scalar_one_or_none()

    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    user = await db.get(User, reset_token.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    user.hashed_password = hash_password(body.new_password)
    reset_token.used = True
    await db.commit()

    return {"message": "Password updated. You can now sign in."}
