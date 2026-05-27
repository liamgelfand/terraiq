"""Class 6 medium-duty — box / straight truck (urban delivery profile)."""
from __future__ import annotations

from models.fuel_map import BSFCMap
from data.vehicle_profiles.freightliner_2022 import Freightliner2022


class MediumDutyClass6(Freightliner2022):
    name = "Class 6 Medium Duty Box"
    vehicle_type = "truck"
    tare_mass_kg = 7_500.0
    mass_kg = 11_793.0
    drag_coefficient = 0.45
    frontal_area_m2 = 6.2
    rolling_resistance = 0.008
    max_power_kw = 260.0
    max_speed_ms = 27.8  # ~100 km/h

    # Shorter ratio stack approximation — reuse shape, scale power envelope in BSFC usage via limits
    gear_ratios = [
        12.0, 9.5, 7.5, 6.0, 4.8, 3.8,
        3.0, 2.4, 1.9, 1.5, 1.2, 1.0
    ]
    final_drive_ratio = 4.10
    wheel_radius_m = 0.431  # 19.5" common on MD trucks

    def get_bsfc_map(self) -> BSFCMap:
        """Smaller-displacement diesel — reuse map shape; solver still uses power limits."""
        return super().get_bsfc_map()
