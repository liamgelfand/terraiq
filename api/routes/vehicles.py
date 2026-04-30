from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])

VEHICLES = [
    {
        "id": "freightliner_2022",
        "name": "Freightliner Cascadia 2022",
        "type": "Class 8 Semi-Truck",
        "mass_kg": 36287,
        "max_speed_kmh": 105,
        "description": "Aerodynamic long-haul tractor, Cd=0.36, validated against NREL Fleet DNA",
    }
]


@router.get("")
async def list_vehicles() -> list:
    return VEHICLES
