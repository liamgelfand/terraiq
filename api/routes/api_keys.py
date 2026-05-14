from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db, require_fleet_admin
from api.models.api_key import ApiKey
from api.schemas.api_key import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyResponse
from api.services.audit import record_audit_event

router = APIRouter(prefix="/api/keys", tags=["api-keys"])


def _generate_key() -> tuple[str, str, str]:
    raw_key = "tiq_" + secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:16] + "..."
    return raw_key, key_hash, key_prefix


@router.post("", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_api_key(
    body: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_fleet_admin),
) -> dict:
    user, fleet = admin
    raw_key, key_hash, key_prefix = _generate_key()

    api_key = ApiKey(
        fleet_id=fleet.id,
        name=body.name,
        fleet_name=fleet.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    await record_audit_event(
        db,
        fleet_id=fleet.id,
        actor_user_id=user.id,
        action="api_key.created",
        resource_type="api_key",
        resource_id=api_key.id,
        details={"name": body.name},
    )

    return {
        "id": api_key.id,
        "name": api_key.name,
        "fleet_name": api_key.fleet_name,
        "key_prefix": api_key.key_prefix,
        "raw_key": raw_key,
        "created_at": api_key.created_at,
    }


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[ApiKey]:
    user, fleet = current_user
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.fleet_id == fleet.id)
        .order_by(ApiKey.created_at.desc())
    )
    return list(result.scalars().all())


@router.delete("/{key_id}", status_code=204, response_class=Response)
async def revoke_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_fleet_admin),
) -> Response:
    user, fleet = admin
    api_key = await db.get(ApiKey, key_id)
    if not api_key or api_key.fleet_id != fleet.id:
        raise HTTPException(status_code=404, detail="API key not found")
    api_key.is_active = False
    await db.commit()
    await record_audit_event(
        db,
        fleet_id=fleet.id,
        actor_user_id=user.id,
        action="api_key.revoked",
        resource_type="api_key",
        resource_id=api_key.id,
        details=None,
    )
    return Response(status_code=204)
