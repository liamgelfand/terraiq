from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import create_access_token, hash_password, verify_password
from api.config import settings
from api.deps import get_current_user, get_db, is_founder_email, require_fleet_admin
from api.emailer import send_email
from api.models.fleet import Fleet
from api.models.fleet_invite import FleetInvite
from api.models.password_reset import PasswordResetToken
from api.models.user import User
from api.services.audit import record_audit_event
from api.services.notifications import send_welcome_email
from api.services.onboarding import seed_starter_corridors
from api.services.plans import apply_founder_plan
from api.schemas.auth import (
    AcceptInviteRequest,
    ChangePasswordRequest,
    FleetUpdateRequest,
    ForgotPasswordRequest,
    InviteInfoResponse,
    LoginRequest,
    OnboardingRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_payload(user: User, fleet: Fleet | None) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "fleet_id": user.fleet_id,
        "fleet_name": fleet.name if fleet else "",
        "role": user.role,
        "onboarding_completed": user.onboarding_completed,
        "is_founder": is_founder_email(user.email),
    }


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> dict:
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    fleet = Fleet(name=body.fleet_name)
    apply_founder_plan(fleet, body.email)
    db.add(fleet)
    await db.flush()  # populate fleet.id before using it

    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        fleet_id=fleet.id,
        role="admin",
        onboarding_completed=False,
    )
    db.add(user)
    await seed_starter_corridors(db, fleet.id)
    await db.commit()
    await db.refresh(user)

    try:
        await send_welcome_email(user.email, user.full_name, fleet.name)
    except Exception:
        logger.exception("Welcome email failed for %s", user.email)

    token = create_access_token(user.id, user.fleet_id)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    fleet = await db.get(Fleet, user.fleet_id)
    if fleet:
        apply_founder_plan(fleet, user.email)
        await db.commit()

    token = create_access_token(user.id, user.fleet_id)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/invite-info", response_model=InviteInfoResponse)
async def invite_info(token: str, db: AsyncSession = Depends(get_db)) -> dict:
    if not token.strip():
        raise HTTPException(status_code=422, detail="token query parameter required")
    th = hashlib.sha256(token.encode()).hexdigest()
    result = await db.execute(select(FleetInvite).where(FleetInvite.token_hash == th))
    inv = result.scalar_one_or_none()
    if not inv or inv.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired invitation")
    fleet = await db.get(Fleet, inv.fleet_id)
    return {"fleet_name": fleet.name if fleet else "", "email": inv.email}


@router.post("/accept-invite", response_model=TokenResponse, status_code=201)
async def accept_invite(body: AcceptInviteRequest, db: AsyncSession = Depends(get_db)) -> dict:
    th = hashlib.sha256(body.token.encode()).hexdigest()
    result = await db.execute(select(FleetInvite).where(FleetInvite.token_hash == th))
    inv = result.scalar_one_or_none()
    if not inv or inv.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired invitation")

    email_norm = inv.email
    taken = await db.execute(select(User).where(User.email == email_norm))
    if taken.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered. Sign in instead")

    user = User(
        email=email_norm,
        full_name=body.full_name,
        hashed_password=hash_password(body.new_password),
        fleet_id=inv.fleet_id,
        role="member",
        onboarding_completed=False,
    )
    db.add(user)
    await db.execute(delete(FleetInvite).where(FleetInvite.id == inv.id))
    await db.commit()
    await db.refresh(user)

    tok = create_access_token(user.id, user.fleet_id)
    return {"access_token": tok, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: tuple[User, Fleet] = Depends(get_current_user),
) -> dict:
    user, fleet = current_user
    return _user_payload(user, fleet)


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

        base = settings.public_app_url.rstrip("/")
        reset_url = f"{base}/?reset_token={raw_token}"

        html_body = (
            f"<p>Hi,</p><p>You asked to reset your TerraIQ password.</p>"
            f'<p><a href="{reset_url}">Click here to set a new password</a></p>'
            f"<p>If you did not request this, you can ignore this email.</p>"
            f"<p>This link expires in 1 hour.</p>"
        )
        sent = await send_email("Reset your TerraIQ password", html_body, user.email)
        if not sent:
            logger.warning(
                "\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                " PASSWORD RESET (email not configured — use link below)\n"
                f" User  : {user.email}\n"
                f" Link  : {reset_url}\n"
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


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    body: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    user, fleet = current_user
    u = await db.get(User, user.id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.full_name = body.full_name
    await db.commit()
    await db.refresh(u)
    f = await db.get(Fleet, u.fleet_id)
    return _user_payload(u, f)


@router.patch("/fleet", response_model=UserResponse)
async def update_fleet_name(
    body: FleetUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_fleet_admin),
) -> dict:
    user, fleet = admin
    f = await db.get(Fleet, fleet.id)
    if not f:
        raise HTTPException(status_code=404, detail="Fleet not found")
    old_name = f.name
    f.name = body.fleet_name
    await db.commit()
    u = await db.get(User, user.id)
    await db.refresh(f)
    await record_audit_event(
        db,
        fleet_id=fleet.id,
        actor_user_id=user.id,
        action="fleet.renamed",
        resource_type="fleet",
        resource_id=fleet.id,
        details={"from": old_name, "to": body.fleet_name},
    )
    return _user_payload(u, f)


@router.post("/change-password", status_code=200)
async def change_password(
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    user, _fleet = current_user
    u = await db.get(User, user.id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(body.current_password, u.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    u.hashed_password = hash_password(body.new_password)
    await db.commit()
    return {"message": "Password updated."}


@router.patch("/onboarding", response_model=UserResponse)
async def update_onboarding(
    body: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    user, fleet = current_user
    u = await db.get(User, user.id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.onboarding_completed = body.onboarding_completed
    await db.commit()
    await db.refresh(u)
    f = await db.get(Fleet, u.fleet_id)
    return _user_payload(u, f)
