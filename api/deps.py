from __future__ import annotations

import hashlib
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


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
