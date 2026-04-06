"""
Vehicle profile for a 2022 Freightliner Cascadia with Detroit DD15 engine.

Specs sourced from:
- Freightliner Cascadia spec sheet (2022)
- Detroit DD15 engine data: 505 HP / 1850 lb-ft peak torque
- NREL Class 8 truck reference vehicle parameters

This is the primary validation vehicle for Phase 1.
Laden mass assumes a typical 34,000 kg GVW (75,000 lb) freight load.
"""

import numpy as np
from models.fuel_map import BSFCMap
from data.vehicle_profiles.base_profile import VehicleProfile


class Freightliner2022(VehicleProfile):

    # Identity
    name = "2022 Freightliner Cascadia DD15"
    vehicle_type = "truck"

    # Mass and geometry (laden — 34,000 kg GVW)
    mass_kg = 34_000.0
    drag_coefficient = 0.36         # Cascadia aero package
    frontal_area_m2 = 9.0           # Class 8 truck frontal area
    rolling_resistance = 0.006      # low-rolling-resistance tires

    # Drivetrain — Detroit DT12 automated transmission (12-speed)
    gear_ratios = [
        14.94, 11.73, 9.48, 7.45, 5.94, 4.67,
        3.63, 2.85, 2.24, 1.76, 1.34, 1.00
    ]
    final_drive_ratio = 2.64
    wheel_radius_m = 0.508          # 22.5" rim + tire (1.0m diameter)

    # Performance limits
    max_power_kw = 375.0            # DD15 505 HP
    max_speed_ms = 29.1             # 65 mph governed (105 km/h)
    max_accel_ms2 = 0.8             # comfortable fleet driving standard
    max_decel_ms2 = 1.5             # service brake comfort limit

    # No regenerative braking (ICE only)
    regen_efficiency = 0.0

    def get_bsfc_map(self) -> BSFCMap:
        """
        Returns a BSFC map for the Detroit DD15 engine.

        Values are representative of a modern large-displacement diesel
        derived from published SAE papers and engine manufacturer data.
        Units: g/kWh at given (RPM, load_fraction) operating point.

        The map covers:
          RPM axis:  600–2100 rpm (idle to governed)
          Load axis: 0.0–1.0 (fraction of peak torque at that RPM)

        Minimum BSFC (sweet spot) is ~185 g/kWh at ~1200 RPM, 70–80% load —
        typical of a well-loaded highway cruise condition.
        """
        rpm_points = np.array([600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2100])
        load_points = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

        # BSFC in g/kWh: rows = RPM, cols = load fraction
        # High at idle/light load, minimum in the 1000-1400 RPM / 60-80% load region
        bsfc_data = np.array([
            # load: 0.0   0.1   0.2   0.3   0.4   0.5   0.6   0.7   0.8   0.9   1.0
            [420,  380,  330,  295,  270,  255,  248,  250,  258,  272,  295],  # 600 rpm
            [370,  320,  285,  262,  245,  235,  228,  228,  233,  243,  260],  # 800 rpm
            [330,  285,  255,  235,  220,  210,  205,  203,  206,  215,  230],  # 1000 rpm
            [310,  268,  240,  220,  205,  196,  190,  188,  190,  198,  212],  # 1200 rpm
            [315,  272,  244,  224,  208,  198,  192,  190,  193,  202,  218],  # 1400 rpm
            [325,  282,  254,  234,  218,  207,  201,  199,  202,  212,  228],  # 1600 rpm
            [340,  296,  266,  246,  230,  218,  212,  210,  213,  224,  242],  # 1800 rpm
            [360,  314,  282,  261,  244,  232,  226,  224,  227,  238,  257],  # 2000 rpm
            [375,  328,  295,  273,  256,  244,  237,  235,  238,  250,  270],  # 2100 rpm
        ], dtype=float)

        return BSFCMap(rpm_points=rpm_points, load_points=load_points, bsfc_data=bsfc_data)

    def get_gear(self, speed_ms: float, grade: float) -> int:
        """
        Gear lookup table for the DT12 12-speed automated transmission.
        Returns 0-based gear index.
        Biases toward lower gears on significant grades to keep RPM in the
        efficient 1000–1400 range.
        """
        speed_kmh = speed_ms * 3.6

        if speed_kmh < 10:
            return 0
        elif speed_kmh < 20:
            return 1 if grade < 0.03 else 0
        elif speed_kmh < 30:
            return 2 if grade < 0.03 else 1
        elif speed_kmh < 40:
            return 3 if grade < 0.02 else 2
        elif speed_kmh < 50:
            return 4 if grade < 0.02 else 3
        elif speed_kmh < 60:
            return 6 if grade < 0.01 else 5
        elif speed_kmh < 75:
            return 8 if grade < 0.01 else 7
        elif speed_kmh < 90:
            return 10 if grade < 0.005 else 9
        else:
            return 11 if grade <= 0.0 else 10
