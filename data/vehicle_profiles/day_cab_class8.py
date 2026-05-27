"""Class 8 day cab — regional / P&D; lighter tare than sleeper."""
from __future__ import annotations

from data.vehicle_profiles.freightliner_2022 import Freightliner2022


class DayCabClass8(Freightliner2022):
    name = "Class 8 Day Cab (regional)"
    vehicle_type = "truck"
    tare_mass_kg = 15_000.0
    mass_kg = 31_751.0
    drag_coefficient = 0.38
    frontal_area_m2 = 8.6
