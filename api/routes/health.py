from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from api.version_info import APP_VERSION

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Liveness probe — process is up. Keep the body stable for existing monitors."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)) -> dict:
    """Readiness probe — database and Redis are reachable."""
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc

    try:
        from api.ratelimit import _get_redis  # noqa: PLC0415

        redis = _get_redis()
        pong = await redis.ping()
        if not pong:
            raise RuntimeError("redis ping returned falsy")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="redis unavailable") from exc

    return {"status": "ready", "version": APP_VERSION}
