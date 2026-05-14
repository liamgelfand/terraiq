"""Fleet audit trail (async API paths)."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.audit_event import AuditEvent


async def record_audit_event(
    db: AsyncSession,
    *,
    fleet_id: str,
    actor_user_id: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditEvent(
            fleet_id=fleet_id,
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )
    )
    await db.commit()
