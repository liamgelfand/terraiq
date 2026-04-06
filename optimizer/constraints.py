"""
Constraint helpers for the MPC optimizer.

Centralizes the rules the optimizer must respect:
- Speed must stay within legal limits
- Acceleration and deceleration must stay within comfort bounds
- Speed must not go below a minimum (truck never stops on open road)

These are applied as inequality constraints in the CasADi Opti problem.
"""

from dataclasses import dataclass
import numpy as np


# Minimum cruising speed — truck doesn't come to a full stop on open highway
V_MIN_MS = 5.0   # m/s (~18 km/h)


@dataclass
class RouteConstraints:
    """
    Per-step constraint arrays for a resampled route.

    All arrays have length n_steps, aligned with the optimizer's
    spatial discretization grid.
    """
    n_steps: int
    speed_upper_ms: np.ndarray   # max speed at each step (min of limit + vehicle max)
    speed_lower_ms: np.ndarray   # min speed at each step
    max_accel_ms2: float         # max acceleration (scalar, from vehicle profile)
    max_decel_ms2: float         # max deceleration (scalar, from vehicle profile)


def build_route_constraints(
    distances: np.ndarray,
    speed_limits_ms: np.ndarray,
    max_vehicle_speed_ms: float,
    max_accel_ms2: float,
    max_decel_ms2: float,
    v_min_ms: float = V_MIN_MS,
) -> RouteConstraints:
    """
    Build the RouteConstraints object for a uniformly sampled route.

    Args:
        distances: 1D array of spatial sample points (m)
        speed_limits_ms: speed limit at each sample point (m/s)
        max_vehicle_speed_ms: vehicle governed top speed (m/s)
        max_accel_ms2: vehicle max comfortable acceleration
        max_decel_ms2: vehicle max comfortable deceleration
        v_min_ms: minimum allowed speed

    Returns:
        RouteConstraints ready to pass to the optimizer
    """
    n = len(distances)
    upper = np.minimum(speed_limits_ms, max_vehicle_speed_ms)
    lower = np.full(n, v_min_ms)
    lower = np.minimum(lower, upper - 0.1)  # ensure lower < upper always

    return RouteConstraints(
        n_steps=n,
        speed_upper_ms=upper,
        speed_lower_ms=lower,
        max_accel_ms2=max_accel_ms2,
        max_decel_ms2=max_decel_ms2,
    )
