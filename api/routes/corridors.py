from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db
from api.models.saved_corridor import SavedCorridor
from api.schemas.corridors import CorridorCreate, CorridorResponse, CorridorUpdate

router = APIRouter(prefix="/api/corridors", tags=["corridors"])


@router.post("", response_model=CorridorResponse, status_code=201)
async def create_corridor(
    body: CorridorCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _user, fleet = current_user
    row = SavedCorridor(
        id=str(uuid.uuid4()),
        fleet_id=fleet.id,
        name=body.name.strip(),
        origin=body.origin.strip(),
        destination=body.destination.strip(),
        vehicle_id=body.vehicle_id,
        load_kg=body.load_kg,
        time_budget_fraction=body.time_budget_fraction,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("", response_model=list[CorridorResponse])
async def list_corridors(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _user, fleet = current_user
    res = await db.execute(
        select(SavedCorridor)
        .where(SavedCorridor.fleet_id == fleet.id)
        .order_by(SavedCorridor.name)
    )
    return list(res.scalars().all())


@router.get("/{corridor_id}", response_model=CorridorResponse)
async def get_corridor(
    corridor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _user, fleet = current_user
    row = await db.get(SavedCorridor, corridor_id)
    if not row or row.fleet_id != fleet.id:
        raise HTTPException(status_code=404, detail="Corridor not found")
    return row


@router.patch("/{corridor_id}", response_model=CorridorResponse)
async def update_corridor(
    corridor_id: str,
    body: CorridorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _user, fleet = current_user
    row = await db.get(SavedCorridor, corridor_id)
    if not row or row.fleet_id != fleet.id:
        raise HTTPException(status_code=404, detail="Corridor not found")
    data = body.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        row.name = data["name"].strip()
    if "origin" in data and data["origin"] is not None:
        row.origin = data["origin"].strip()
    if "destination" in data and data["destination"] is not None:
        row.destination = data["destination"].strip()
    if "vehicle_id" in data and data["vehicle_id"] is not None:
        row.vehicle_id = data["vehicle_id"]
    if "load_kg" in data:
        row.load_kg = data["load_kg"]
    if "time_budget_fraction" in data and data["time_budget_fraction"] is not None:
        row.time_budget_fraction = data["time_budget_fraction"]
    row.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/{corridor_id}", status_code=204, response_class=Response)
async def delete_corridor(
    corridor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Response:
    _user, fleet = current_user
    row = await db.get(SavedCorridor, corridor_id)
    if not row or row.fleet_id != fleet.id:
        raise HTTPException(status_code=404, detail="Corridor not found")
    await db.delete(row)
    await db.commit()
    return Response(status_code=204)


@router.post("/{corridor_id}/duplicate", response_model=CorridorResponse, status_code=201)
async def duplicate_corridor(
    corridor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _user, fleet = current_user
    src = await db.get(SavedCorridor, corridor_id)
    if not src or src.fleet_id != fleet.id:
        raise HTTPException(status_code=404, detail="Corridor not found")
    base_name = src.name
    dup = SavedCorridor(
        id=str(uuid.uuid4()),
        fleet_id=fleet.id,
        name=f"{base_name[:160]} (copy {uuid.uuid4().hex[:6]})",
        origin=src.origin,
        destination=src.destination,
        vehicle_id=src.vehicle_id,
        load_kg=src.load_kg,
        time_budget_fraction=src.time_budget_fraction,
    )
    db.add(dup)
    await db.commit()
    await db.refresh(dup)
    return dup
