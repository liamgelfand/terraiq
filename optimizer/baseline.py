"""
Baseline simulator: constant-speed human driving.

Simulates a driver who holds the legal speed limit at each point on the route,
decelerating to the next limit when it drops and accelerating when it rises.
This is the benchmark every optimizer result is compared against.

The baseline is intentionally simple and slightly optimistic for human drivers —
it assumes perfect anticipation of speed limit changes. Real human driving
would consume slightly more due to reaction delays and unnecessary acceleration.
"""

from __future__ import annotations

import numpy as np

from models.world_model import WorldModel
from models.vehicle_model import VehicleModel
from data.vehicle_profiles.base_profile import VehicleProfile


def build_baseline_speed_profile(
    world: WorldModel,
    vehicle: VehicleProfile,
    target_speed_ms: float | None = None,
) -> np.ndarray:
    """
    Build a constant-speed baseline profile.

    At each route point the vehicle travels at:
    - `target_speed_ms` if provided (ignores speed limits — for fixed-speed tests)
    - otherwise the legal speed limit at that point, clamped to the
      vehicle's governed top speed

    Acceleration between consecutive points is implicitly handled by the
    physics engine when it computes the inertia force term.

    Args:
        world: WorldModel with speed limit and route data
        vehicle: VehicleProfile for top speed clamping
        target_speed_ms: optional override (e.g. 88 km/h = 24.4 m/s for
                         a constant-speed validation run)

    Returns:
        numpy array of speeds in m/s, one per route point
    """
    if target_speed_ms is not None:
        speed = np.full(world.n_points, min(target_speed_ms, vehicle.max_speed_ms))
    else:
        speed = np.minimum(world.speed_limit_ms, vehicle.max_speed_ms)

    # Enforce max acceleration/deceleration between consecutive points
    speed = _enforce_accel_limits(speed, world.distance_m, vehicle)

    return speed


def _enforce_accel_limits(
    speed: np.ndarray,
    distance_m: np.ndarray,
    vehicle: VehicleProfile,
) -> np.ndarray:
    """
    Forward-backward pass to clamp speed changes to vehicle comfort limits.
    Ensures no segment has acceleration > max_accel_ms2 or
    deceleration > max_decel_ms2.
    """
    speed = speed.copy()
    n = len(speed)
    segment_lengths = np.diff(distance_m)

    # Forward pass — limit acceleration
    for i in range(1, n):
        dx = segment_lengths[i - 1]
        v_prev = speed[i - 1]
        v_max_from_accel = np.sqrt(max(v_prev**2 + 2 * vehicle.max_accel_ms2 * dx, 0.0))
        speed[i] = min(speed[i], v_max_from_accel)

    # Backward pass — limit deceleration (anticipate upcoming lower limits)
    for i in range(n - 2, -1, -1):
        dx = segment_lengths[i]
        v_next = speed[i + 1]
        v_max_from_decel = np.sqrt(max(v_next**2 + 2 * vehicle.max_decel_ms2 * dx, 0.0))
        speed[i] = min(speed[i], v_max_from_decel)

    return np.maximum(speed, 0.5)  # never come to a complete stop on open road
