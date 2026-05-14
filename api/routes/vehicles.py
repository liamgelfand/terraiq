from __future__ import annotations

from fastapi import APIRouter

from api.vehicle_factory import list_public_vehicles

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


@router.get("")
async def list_vehicles() -> list:
    return list_public_vehicles()
