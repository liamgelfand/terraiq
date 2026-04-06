"""
SimulationRunner: end-to-end pipeline from coordinates to fuel results.

Usage:
    runner = SimulationRunner(vehicle=Freightliner2022())
    result = runner.run(
        origin=(41.1, -111.9),      # Ogden, UT
        destination=(38.8, -120.9), # Placerville, CA  (crosses Donner Pass)
    )
    result.print_summary()
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from data.route_fetcher import fetch_route
from data.vehicle_profiles.base_profile import VehicleProfile
from models.world_model import WorldModel
from models.vehicle_model import VehicleModel
from optimizer.baseline import build_baseline_speed_profile


@dataclass
class SimulationResult:
    """All outputs from a single simulation run."""

    # Route info
    route_name: str
    total_distance_km: float
    elevation_gain_m: float
    elevation_loss_m: float

    # Speed profile used
    speed_profile_ms: np.ndarray

    # Fuel results
    total_fuel_liters: float
    total_fuel_kg: float
    fuel_per_100km: float

    # Per-segment arrays for plotting
    distances_m: np.ndarray
    elevations_m: np.ndarray
    grades: np.ndarray
    speed_limits_ms: np.ndarray
    segment_fuel_L: np.ndarray
    segment_power_kw: np.ndarray

    # Coordinates for map rendering
    lat: np.ndarray = field(default_factory=lambda: np.array([]))
    lon: np.ndarray = field(default_factory=lambda: np.array([]))

    # Metadata
    vehicle_name: str = ""
    elapsed_seconds: float = 0.0

    def print_summary(self):
        print("\n" + "="*60)
        print(f"  {self.route_name}")
        print("="*60)
        print(f"  Vehicle:         {self.vehicle_name}")
        print(f"  Distance:        {self.total_distance_km:.1f} km")
        print(f"  Elevation:       +{self.elevation_gain_m:.0f}m / -{self.elevation_loss_m:.0f}m")
        print(f"  Avg speed:       {np.mean(self.speed_profile_ms)*3.6:.1f} km/h")
        print(f"  Max speed:       {np.max(self.speed_profile_ms)*3.6:.1f} km/h")
        print("-"*60)
        print(f"  Total fuel:      {self.total_fuel_liters:.2f} L")
        print(f"  Fuel efficiency: {self.fuel_per_100km:.2f} L/100km")
        print(f"  CO2 (approx):    {self.total_fuel_liters * 2.68:.1f} kg")
        print("="*60)
        print(f"  Simulation completed in {self.elapsed_seconds:.1f}s")
        print()


class SimulationRunner:
    """
    Runs a full simulation for a given vehicle on a given route.

    Currently supports baseline (constant-speed) simulation.
    The MPC optimizer will be added as a second mode in a future stage.
    """

    def __init__(self, vehicle: VehicleProfile):
        self.vehicle = vehicle
        self.vehicle_model = VehicleModel(vehicle)

    def run(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        route_name: str = "Route",
        target_speed_ms: float | None = None,
        network_type: str = "drive",
        default_speed_limit_kmh: float = 90.0,
    ) -> SimulationResult:
        """
        Fetch the route, build the baseline speed profile, and compute fuel.

        Args:
            origin: (lat, lon) start point
            destination: (lat, lon) end point
            route_name: label for the result summary
            target_speed_ms: if set, drive at this fixed speed instead of
                             following speed limits
            network_type: OSMnx network type
            default_speed_limit_kmh: fallback when OSM data is missing

        Returns:
            SimulationResult with all outputs
        """
        t0 = time.time()

        print(f"\nRunning baseline simulation: {route_name}")
        route_points = fetch_route(
            origin,
            destination,
            network_type=network_type,
            default_speed_limit_kmh=default_speed_limit_kmh,
        )

        world = WorldModel.from_route_points(route_points)
        print(world.summary())

        speed_profile = build_baseline_speed_profile(
            world, self.vehicle, target_speed_ms=target_speed_ms
        )

        print("Computing fuel consumption...")
        fuel_result = self.vehicle_model.compute_fuel_consumption(world, speed_profile)

        elapsed = time.time() - t0

        return SimulationResult(
            route_name=route_name,
            total_distance_km=world.total_distance_km,
            elevation_gain_m=world.elevation_gain_m,
            elevation_loss_m=world.elevation_loss_m,
            speed_profile_ms=speed_profile,
            total_fuel_liters=fuel_result["total_fuel_liters"],
            total_fuel_kg=fuel_result["total_fuel_kg"],
            fuel_per_100km=fuel_result["fuel_per_100km"],
            distances_m=world.distance_m,
            elevations_m=world.elevation_m,
            grades=world.grade,
            speed_limits_ms=world.speed_limit_ms,
            segment_fuel_L=fuel_result["segment_fuel_L"],
            segment_power_kw=fuel_result["segment_power_kw"],
            lat=world.lat,
            lon=world.lon,
            vehicle_name=self.vehicle.name,
            elapsed_seconds=elapsed,
        )
