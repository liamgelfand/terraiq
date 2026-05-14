"""Maps `vehicle_id` strings (API + simulation) to vehicle profile classes."""
from __future__ import annotations

from collections.abc import Callable

from data.vehicle_profiles.freightliner_2022 import Freightliner2022
from data.vehicle_profiles.day_cab_class8 import DayCabClass8
from data.vehicle_profiles.medium_duty_6 import MediumDutyClass6


def _registry() -> dict[str, Callable[[], object]]:
    return {
        "freightliner_2022": lambda: Freightliner2022(),
        "daycab_class8": lambda: DayCabClass8(),
        "medium_duty_6": lambda: MediumDutyClass6(),
    }


def get_vehicle_instance(vehicle_id: str | None):
    """Return a fresh vehicle profile instance. Defaults to Freightliner."""
    reg = _registry()
    factory = reg.get(vehicle_id or "", reg["freightliner_2022"])
    return factory()


def list_public_vehicles() -> list[dict]:
    """Static metadata for GET /api/vehicles."""
    return [
        {
            "id": "freightliner_2022",
            "name": "Freightliner Cascadia 2022 (sleeper)",
            "type": "Class 8 Semi-Truck",
            "mass_kg": 36287,
            "max_speed_kmh": 105,
            "description": "Long-haul tractor, NREL-aligned reference vehicle.",
        },
        {
            "id": "daycab_class8",
            "name": "Class 8 day cab",
            "type": "Class 8 Day Cab",
            "mass_kg": 31751,
            "max_speed_kmh": 105,
            "description": "Regional / P&D — lighter tare, shorter wheelbase assumption.",
        },
        {
            "id": "medium_duty_6",
            "name": "Class 6 medium-duty box",
            "type": "Class 6 Truck",
            "mass_kg": 11793,
            "max_speed_kmh": 100,
            "description": "Box / straight truck urban and regional delivery.",
        },
    ]
