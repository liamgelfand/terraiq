"""
MPC Optimizer: fuel-optimal speed trajectory using CasADi + IPOPT.

For Phase 1 simulation, this solves a *global* optimization over the full route
rather than receding-horizon MPC. This gives the theoretical best-case fuel
savings achievable with perfect terrain knowledge — the ideal ceiling for
what the product can deliver.

The optimization problem (spatially discretized):
    minimize    sum_i  max(F_total_i, 0) * ds        [propulsive work]
    subject to  v_min  <= v[i] <= speed_limit[i]     [speed bounds]
                a[i]   <= max_accel                   [comfort acceleration]
                -a[i]  <= max_decel                   [comfort deceleration]

where:
    v[i]      = speed at spatial step i (decision variable)
    ds        = spatial step size (meters)
    a[i]      = (v[i]^2 - v[i-1]^2) / (2*ds)        [kinematic accel]
    F_total   = F_aero + F_roll + F_grade + F_inertia [longitudinal forces]

The objective is propulsive work (J), which is proportional to fuel consumption
when BSFC is assumed approximately constant near the highway cruise operating
point. This is a valid approximation for Class 8 trucks at 70–110 km/h where
the engine operates in its efficient zone.

Solver: IPOPT (bundled with CasADi). Typical solve time: 5–30 seconds for
a 100–300 km route at 100m spatial steps.
"""

from __future__ import annotations

import numpy as np

try:
    import casadi as ca
    CASADI_AVAILABLE = True
except ImportError:
    CASADI_AVAILABLE = False

from models.world_model import WorldModel
from data.vehicle_profiles.base_profile import VehicleProfile
from optimizer.constraints import build_route_constraints

# Physics constants
RHO_AIR = 1.225   # kg/m³
G = 9.81          # m/s²

# Spatial discretization — 100m steps balance accuracy with solve time
DEFAULT_SPATIAL_STEP_M = 100.0


def optimize_full_route(
    world: WorldModel,
    vehicle: VehicleProfile,
    spatial_step_m: float = DEFAULT_SPATIAL_STEP_M,
    verbose: bool = False,
) -> np.ndarray:
    """
    Compute the globally fuel-optimal speed trajectory for the full route.

    Resamples the route at uniform spatial steps, solves the NLP with IPOPT,
    then interpolates the result back onto the original world model distance grid.

    Args:
        world: WorldModel with grade, speed limits, and distance data
        vehicle: VehicleProfile with mass, aero, and performance specs
        spatial_step_m: spatial discretization step in meters (smaller = more
                        accurate but slower; 50–200m is a good range)
        verbose: if True, print IPOPT solver output

    Returns:
        Speed profile in m/s, one value per point in world.distance_m
    """
    if not CASADI_AVAILABLE:
        raise ImportError("CasADi is required for the optimizer. Run: pip install casadi")

    # Resample route at uniform spatial steps
    n_steps = max(int(world.total_distance_m / spatial_step_m) + 1, 10)
    distances = np.linspace(0.0, world.total_distance_m, n_steps)
    ds = distances[1] - distances[0]

    grades = np.interp(distances, world.distance_m, world.grade)
    speed_limits = np.interp(distances, world.distance_m, world.speed_limit_ms)

    constraints = build_route_constraints(
        distances=distances,
        speed_limits_ms=speed_limits,
        max_vehicle_speed_ms=vehicle.max_speed_ms,
        max_accel_ms2=vehicle.max_accel_ms2,
        max_decel_ms2=vehicle.max_decel_ms2,
    )

    print(f"  Solving NLP: {n_steps} steps at {spatial_step_m:.0f}m resolution...", flush=True)

    opt_speeds = _solve_nlp(
        n_steps=n_steps,
        ds=ds,
        grades=grades,
        constraints=constraints,
        vehicle=vehicle,
        verbose=verbose,
    )

    # Interpolate back onto the original world model distance grid
    return np.interp(world.distance_m, distances, opt_speeds)


def _solve_nlp(
    n_steps: int,
    ds: float,
    grades: np.ndarray,
    constraints,
    vehicle: VehicleProfile,
    verbose: bool,
) -> np.ndarray:
    """
    Build and solve the CasADi NLP.

    Returns the optimal speed array at the n_steps spatial points.
    """
    opti = ca.Opti()

    # Decision variables: speed at each spatial step
    v = opti.variable(n_steps)

    # Vehicle constants
    m   = vehicle.mass_kg
    Cd  = vehicle.drag_coefficient
    A   = vehicle.frontal_area_m2
    Crr = vehicle.rolling_resistance

    # Objective: total propulsive work (proportional to fuel)
    total_work = 0.0
    for i in range(1, n_steps):
        v_mid = (v[i] + v[i - 1]) / 2.0

        # Kinematic acceleration from speed change over spatial step
        accel = (v[i] ** 2 - v[i - 1] ** 2) / (2.0 * ds)

        # Longitudinal forces at midpoint
        f_aero    = 0.5 * RHO_AIR * Cd * A * v_mid ** 2
        f_roll    = Crr * m * G
        f_grade   = m * G * grades[i]           # sin(arctan(g)) ≈ g for |g| < 0.2
        f_inertia = m * accel

        f_total = f_aero + f_roll + f_grade + f_inertia

        # Only penalize positive force — engine only burns fuel under positive load.
        # fmax is smooth enough for IPOPT via an internal reformulation.
        total_work = total_work + ca.fmax(f_total * ds, 0.0)

    opti.minimize(total_work)

    # Speed bound constraints
    for i in range(n_steps):
        opti.subject_to(v[i] >= constraints.speed_lower_ms[i])
        opti.subject_to(v[i] <= constraints.speed_upper_ms[i])

    # Acceleration / deceleration comfort constraints
    for i in range(1, n_steps):
        accel = (v[i] ** 2 - v[i - 1] ** 2) / (2.0 * ds)
        opti.subject_to(accel <=  constraints.max_accel_ms2)
        opti.subject_to(accel >= -constraints.max_decel_ms2)

    # Warm start: initialize at speed limits (feasible starting point)
    opti.set_initial(v, constraints.speed_upper_ms)

    # IPOPT solver options
    solver_opts = {
        "ipopt.print_level":    5 if verbose else 0,
        "ipopt.max_iter":       2000,
        "ipopt.tol":            1e-4,
        "ipopt.acceptable_tol": 1e-3,
        "print_time":           1 if verbose else 0,
    }
    opti.solver("ipopt", solver_opts)

    try:
        sol = opti.solve()
        speeds = sol.value(v)
    except RuntimeError as e:
        print(f"  Optimizer did not converge cleanly: {e}", flush=True)
        print("  Using best feasible solution found so far.", flush=True)
        speeds = opti.debug.value(v)

    # Clamp to ensure strict feasibility after solve
    speeds = np.clip(speeds, constraints.speed_lower_ms, constraints.speed_upper_ms)
    return speeds
