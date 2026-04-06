"""
VehicleModel: physics-based fuel consumption engine.

Given a speed profile (array of speeds at each route point) and a WorldModel,
computes the total fuel consumed in liters using:

  1. Longitudinal dynamics: F_total = F_aero + F_roll + F_grade + F_inertia
  2. Required power:        P = F_total * v
  3. Engine operating point: RPM from gear selection, load from power demand
  4. BSFC map lookup:       fuel_rate (g/kWh) -> fuel consumed (g) per step

Constants:
  rho_air = 1.225 kg/m³  (standard atmosphere at sea level)
  g       = 9.81 m/s²
  diesel_density = 0.832 kg/L
"""

from __future__ import annotations

import math

import numpy as np

from data.vehicle_profiles.base_profile import VehicleProfile
from models.world_model import WorldModel

RHO_AIR = 1.225         # kg/m³
G = 9.81                # m/s²
DIESEL_DENSITY_KG_L = 0.832


class VehicleModel:
    """
    Computes fuel consumption for a given vehicle traversing a given route
    at a specified speed profile.
    """

    def __init__(self, vehicle: VehicleProfile):
        self.vehicle = vehicle
        self.bsfc_map = vehicle.get_bsfc_map()

    def compute_fuel_consumption(
        self,
        world: WorldModel,
        speed_profile_ms: np.ndarray,
    ) -> dict:
        """
        Simulate driving the route at the given speed profile and return
        fuel consumption results.

        Args:
            world: WorldModel containing grade, distance, and speed limit arrays
            speed_profile_ms: array of speeds in m/s, one per route point,
                              same length as world.n_points

        Returns:
            dict with:
                total_fuel_liters: total fuel consumed
                total_fuel_kg: same in kg
                fuel_per_km_L: liters per 100 km
                segment_fuel_L: per-segment fuel array
                segment_power_kw: per-segment power demand array
                segment_forces: dict of force component arrays
        """
        if len(speed_profile_ms) != world.n_points:
            raise ValueError(
                f"speed_profile length {len(speed_profile_ms)} must match "
                f"world.n_points {world.n_points}"
            )

        v = np.asarray(speed_profile_ms, dtype=float)
        grade = world.grade
        dist = world.distance_m

        segment_lengths = np.diff(dist)
        n_segments = len(segment_lengths)

        v_mid = (v[:-1] + v[1:]) / 2.0
        grade_mid = (grade[:-1] + grade[1:]) / 2.0
        accel = np.diff(v) / np.maximum(segment_lengths / np.maximum(v_mid, 0.1), 1e-6)

        f_aero = 0.5 * RHO_AIR * self.vehicle.drag_coefficient * self.vehicle.frontal_area_m2 * v_mid**2
        f_roll = self.vehicle.rolling_resistance * self.vehicle.mass_kg * G * np.ones(n_segments)
        f_grade = self.vehicle.mass_kg * G * np.sin(np.arctan(grade_mid))
        f_inertia = self.vehicle.mass_kg * accel

        f_total = f_aero + f_roll + f_grade + f_inertia

        # Clamp negative force (coasting / overrun) — engine produces zero fuel
        # when decelerating on compression. Regen handled separately for hybrids/EVs.
        power_kw = np.maximum(f_total * v_mid, 0.0) / 1000.0

        fuel_segment_L = np.zeros(n_segments)
        for i in range(n_segments):
            if power_kw[i] < 0.5:
                # Engine at idle or overrun — use idle fuel rate
                fuel_segment_L[i] = self._idle_fuel_L(segment_lengths[i], v_mid[i])
                continue

            gear_idx = self.vehicle.get_gear(v_mid[i], grade_mid[i])
            rpm = self._speed_to_rpm(v_mid[i], gear_idx)
            load = self._power_to_load(power_kw[i], rpm)

            bsfc_g_per_kwh = self.bsfc_map.lookup(rpm, load)

            # fuel (g) = BSFC (g/kWh) * power (kW) * time (h)
            time_h = (segment_lengths[i] / max(v_mid[i], 0.1)) / 3600.0
            fuel_g = bsfc_g_per_kwh * power_kw[i] * time_h
            fuel_segment_L[i] = fuel_g / (DIESEL_DENSITY_KG_L * 1000.0)

        # Subtract regen recovery (EVs/hybrids)
        if self.vehicle.regen_efficiency > 0:
            fuel_segment_L = self._apply_regen(
                fuel_segment_L, f_total, v_mid, segment_lengths
            )

        total_fuel_L = float(np.sum(fuel_segment_L))
        total_dist_km = world.total_distance_km

        return {
            "total_fuel_liters": total_fuel_L,
            "total_fuel_kg": total_fuel_L * DIESEL_DENSITY_KG_L,
            "fuel_per_100km": (total_fuel_L / total_dist_km * 100) if total_dist_km > 0 else 0.0,
            "segment_fuel_L": fuel_segment_L,
            "segment_power_kw": power_kw,
            "segment_forces": {
                "aero": f_aero,
                "roll": f_roll,
                "grade": f_grade,
                "inertia": f_inertia,
                "total": f_total,
            },
        }

    def _speed_to_rpm(self, speed_ms: float, gear_idx: int) -> float:
        """
        Convert wheel speed to engine RPM given gear selection.
        RPM = (speed_ms / wheel_radius) * (gear_ratio * final_drive) * (60 / 2π)
        """
        if speed_ms < 0.1:
            return 700.0  # idle
        gear_ratio = self.vehicle.gear_ratios[gear_idx]
        angular_velocity = speed_ms / self.vehicle.wheel_radius_m
        engine_rad_s = angular_velocity * gear_ratio * self.vehicle.final_drive_ratio
        rpm = engine_rad_s * 60.0 / (2.0 * math.pi)
        return float(np.clip(rpm, 600, 2100))

    def _power_to_load(self, power_kw: float, rpm: float) -> float:
        """
        Estimate engine load fraction given power demand and RPM.
        Load = power / max_power_at_rpm (simplified — assumes flat power curve).
        Clamped to [0.05, 1.0].
        """
        if self.vehicle.max_power_kw <= 0:
            return 0.5
        load = power_kw / self.vehicle.max_power_kw
        return float(np.clip(load, 0.05, 1.0))

    def _idle_fuel_L(self, segment_length_m: float, speed_ms: float) -> float:
        """
        Fuel consumed at idle/overrun — approximately 2–3 L/hr for a Class 8 diesel.
        """
        idle_rate_L_per_hr = 2.5
        time_h = (segment_length_m / max(speed_ms, 0.1)) / 3600.0
        return idle_rate_L_per_hr * time_h

    def _apply_regen(
        self,
        fuel_segment_L: np.ndarray,
        f_total: np.ndarray,
        v_mid: np.ndarray,
        segment_lengths: np.ndarray,
    ) -> np.ndarray:
        """
        Subtract fuel equivalent of regenerative braking energy recovery.
        Only applies where f_total < 0 (vehicle is decelerating).
        """
        regen_fuel = np.zeros_like(fuel_segment_L)
        decel_mask = f_total < 0
        braking_power_kw = np.abs(f_total[decel_mask] * v_mid[decel_mask]) / 1000.0
        time_h = (segment_lengths[decel_mask] / np.maximum(v_mid[decel_mask], 0.1)) / 3600.0
        recovered_kwh = braking_power_kw * time_h * self.vehicle.regen_efficiency
        # Convert recovered energy back to equivalent fuel savings
        # Using best-point BSFC as the conversion factor
        min_bsfc = self.bsfc_map.min_bsfc
        fuel_saved_g = recovered_kwh * min_bsfc
        fuel_saved_L = fuel_saved_g / (DIESEL_DENSITY_KG_L * 1000.0)
        regen_fuel[decel_mask] = fuel_saved_L
        return np.maximum(fuel_segment_L - regen_fuel, 0.0)
