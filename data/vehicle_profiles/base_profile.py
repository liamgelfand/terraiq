"""
Abstract base class for all vehicle profiles.

Every vehicle the optimizer works with must implement this interface.
The optimizer and physics engine call only these attributes — they never
depend on vehicle-specific internals.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass
class GearMapEntry:
    """Optimal gear selection for a given speed range and grade range."""
    min_speed_ms: float
    max_speed_ms: float
    min_grade: float
    max_grade: float
    gear: int


class VehicleProfile(ABC):
    """
    Base class defining the interface all vehicle profiles must satisfy.

    Subclasses set concrete values for every attribute. The physics engine
    (vehicle_model.py) and MPC optimizer read these attributes directly.
    """

    # --- Identity ---
    name: str
    vehicle_type: str   # "truck", "car", "hybrid", "ev"

    # --- Mass and geometry ---
    mass_kg: float              # total laden mass (kg) — tare + payload
    tare_mass_kg: float         # unladen (empty) vehicle mass (kg)
    drag_coefficient: float     # aerodynamic Cd (dimensionless)
    frontal_area_m2: float      # frontal cross-section area (m²)
    rolling_resistance: float   # Crr (dimensionless)

    # --- Drivetrain ---
    gear_ratios: list[float]    # list of gear ratios, index 0 = 1st gear
    final_drive_ratio: float    # axle ratio
    wheel_radius_m: float       # effective rolling radius (m)

    # --- Performance limits ---
    max_power_kw: float         # peak engine power (kW)
    max_speed_ms: float         # governed top speed (m/s)
    max_accel_ms2: float        # max comfortable acceleration (m/s²)
    max_decel_ms2: float        # max comfortable deceleration (m/s²)

    # --- Energy recovery ---
    regen_efficiency: float     # 0.0 for ICE; 0.0–1.0 for hybrid/EV

    @abstractmethod
    def get_bsfc_map(self) -> "BSFCMap":
        """Return the BSFC map for this vehicle's engine."""
        ...

    def get_gear(self, speed_ms: float, grade: float) -> int:
        """
        Return the optimal gear for current speed and grade via lookup table.
        Subclasses should override this with a vehicle-specific gear map.
        Default: simplest possible heuristic.
        """
        n_gears = len(self.gear_ratios)
        speed_kmh = speed_ms * 3.6
        idx = min(int(speed_kmh / 15), n_gears - 1)
        if grade > 0.04 and idx > 0:
            idx -= 1
        return max(0, idx)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, mass={self.mass_kg}kg)"
