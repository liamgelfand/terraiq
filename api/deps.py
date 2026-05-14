from __future__ import annotations

import hashlib
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import AsyncSessionLocal

_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate a Bearer JWT and return (User, Fleet).
    Raises 401 if the token is missing or invalid.
    """
    from api.auth import decode_access_token  # noqa: PLC0415
    from api.models.fleet import Fleet  # noqa: PLC0415
    from api.models.user import User  # noqa: PLC0415

    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id: str = payload.get("sub", "")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    fleet = await db.get(Fleet, user.fleet_id)
    if not fleet:
        raise HTTPException(status_code=401, detail="Fleet not found")

    return user, fleet


async def require_fleet_admin(
    current_user=Depends(get_current_user),
):
    """Require JWT user with fleet admin role."""
    user, fleet = current_user
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Fleet administrator role required for this action",
        )
    return user, fleet


async def require_api_key(
    x_api_key: str = Header(alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    """FastAPI dependency that validates an API key from the X-API-Key header."""
    from api.models.api_key import ApiKey  # noqa: PLC0415

    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    api_key.usage_count += 1
    api_key.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    return api_key
