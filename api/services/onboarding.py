"""First-run fleet setup: starter corridors a dispatcher can optimize immediately."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.saved_corridor import SavedCorridor

STARTER_CORRIDORS = (
    {
        "name": "I-70 Denver – Grand Junction",
        "origin": "Denver, CO",
        "destination": "Grand Junction, CO",
    },
    {
        "name": "I-80 Cheyenne – Salt Lake City",
        "origin": "Cheyenne, WY",
        "destination": "Salt Lake City, UT",
    },
)


async def seed_starter_corridors(db: AsyncSession, fleet_id: str) -> list[SavedCorridor]:
    now = datetime.now(timezone.utc)
    rows: list[SavedCorridor] = []
    for spec in STARTER_CORRIDORS:
        row = SavedCorridor(
            id=str(uuid.uuid4()),
            fleet_id=fleet_id,
            name=spec["name"],
            origin=spec["origin"],
            destination=spec["destination"],
            vehicle_id="freightliner_2022",
            time_budget_fraction=1.05,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
        rows.append(row)
    return rows
