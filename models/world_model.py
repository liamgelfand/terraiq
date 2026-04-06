"""
WorldModel: the route as a structured, queryable data object.

Built from a list of RoutePoints produced by route_fetcher.py.
All other components (vehicle model, optimizer, baseline) consume WorldModel —
they never touch raw coordinate data directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from data.route_fetcher import RoutePoint


@dataclass
class WorldModel:
    """
    Structured representation of a route for use by the physics engine
    and optimizer.

    All arrays are parallel — index i corresponds to the same point on the route.
    Distance, elevation, grade, and speed limit are stored as numpy arrays
    for efficient vectorized computation.
    """
    points: list[RoutePoint]

    # Pre-computed numpy arrays for fast access during simulation
    distance_m: np.ndarray = field(init=False)
    elevation_m: np.ndarray = field(init=False)
    grade: np.ndarray = field(init=False)
    speed_limit_ms: np.ndarray = field(init=False)
    lat: np.ndarray = field(init=False)
    lon: np.ndarray = field(init=False)

    def __post_init__(self):
        if len(self.points) < 2:
            raise ValueError("WorldModel requires at least 2 route points.")
        self.distance_m = np.array([p.distance_m for p in self.points])
        self.elevation_m = np.array([p.elevation_m for p in self.points])
        self.grade = np.array([p.grade for p in self.points])
        self.speed_limit_ms = np.array([p.speed_limit_ms for p in self.points])
        self.lat = np.array([p.lat for p in self.points])
        self.lon = np.array([p.lon for p in self.points])

    @property
    def total_distance_m(self) -> float:
        return float(self.distance_m[-1])

    @property
    def total_distance_km(self) -> float:
        return self.total_distance_m / 1000.0

    @property
    def n_points(self) -> int:
        return len(self.points)

    @property
    def elevation_gain_m(self) -> float:
        """Total cumulative elevation gain (uphill only)."""
        deltas = np.diff(self.elevation_m)
        return float(np.sum(deltas[deltas > 0]))

    @property
    def elevation_loss_m(self) -> float:
        """Total cumulative elevation loss (downhill only, positive value)."""
        deltas = np.diff(self.elevation_m)
        return float(np.sum(np.abs(deltas[deltas < 0])))

    @property
    def max_grade(self) -> float:
        return float(np.max(self.grade))

    @property
    def min_grade(self) -> float:
        return float(np.min(self.grade))

    def get_state_at_distance(self, distance_m: float) -> dict:
        """
        Interpolate route state (elevation, grade, speed limit) at any distance
        along the route. Used by the MPC optimizer for lookahead queries.

        Args:
            distance_m: distance from origin in meters

        Returns:
            dict with keys: elevation_m, grade, speed_limit_ms
        """
        distance_m = np.clip(distance_m, 0.0, self.total_distance_m)
        elevation = float(np.interp(distance_m, self.distance_m, self.elevation_m))
        grade = float(np.interp(distance_m, self.distance_m, self.grade))
        speed_limit = float(np.interp(distance_m, self.distance_m, self.speed_limit_ms))
        return {
            "elevation_m": elevation,
            "grade": grade,
            "speed_limit_ms": speed_limit,
        }

    def get_lookahead(
        self,
        current_distance_m: float,
        horizon_m: float,
        n_steps: int,
    ) -> dict[str, np.ndarray]:
        """
        Return arrays of grade and speed limit for the next horizon_m meters,
        sampled at n_steps evenly spaced points.

        This is the primary input to the MPC optimizer at each solve step.

        Args:
            current_distance_m: current position along route
            horizon_m: how far ahead to look (meters)
            n_steps: number of discretization points

        Returns:
            dict with keys: distances, grades, speed_limits, elevations
        """
        end_distance = min(current_distance_m + horizon_m, self.total_distance_m)
        sample_distances = np.linspace(current_distance_m, end_distance, n_steps)

        return {
            "distances": sample_distances,
            "grades": np.interp(sample_distances, self.distance_m, self.grade),
            "speed_limits_ms": np.interp(sample_distances, self.distance_m, self.speed_limit_ms),
            "elevations_m": np.interp(sample_distances, self.distance_m, self.elevation_m),
        }

    def summary(self) -> str:
        return (
            f"Route: {self.total_distance_km:.1f} km | "
            f"{self.n_points} points | "
            f"Elevation: +{self.elevation_gain_m:.0f}m / -{self.elevation_loss_m:.0f}m | "
            f"Max grade: {self.max_grade*100:.1f}% | "
            f"Speed limits: {self.speed_limit_ms.min()*3.6:.0f}–{self.speed_limit_ms.max()*3.6:.0f} km/h"
        )

    @classmethod
    def from_route_points(cls, points: list[RoutePoint]) -> "WorldModel":
        return cls(points=points)
