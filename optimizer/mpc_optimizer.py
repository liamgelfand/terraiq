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
    time_budget_fraction: float = 1.0,
    verbose: bool = False,
) -> np.ndarray:
    """
    Compute the globally fuel-optimal speed trajectory for the full route.

    Resamples the route at uniform spatial steps, solves the NLP with IPOPT,
    then interpolates the result back onto the original world model distance grid.

    Args:
        world: WorldModel with grade, speed limits, and distance data
        vehicle: VehicleProfile with mass, aero, and performance specs
        spatial_step_m: spatial discretization step in meters
        time_budget_fraction: max allowed travel time as a fraction of baseline
                              (1.05 = no more than 5% slower than speed limits).
                              This prevents the optimizer from simply slowing
                              down everywhere to reduce drag.
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

    # Auto-scale: cap at 1000 steps regardless of route length to keep solve time bounded.
    # This adjusts the spatial step upward for long routes (e.g. 200m for 200km, 400m for 400km).
    MAX_STEPS = 1000
    if n_steps > MAX_STEPS:
        spatial_step_m = world.total_distance_m / MAX_STEPS
        n_steps = MAX_STEPS
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

    # Baseline travel time: sum over n_steps-1 SEGMENTS (not n_steps points)
    # Using midpoint speed limit per segment to match the optimizer's v_mid convention
    seg_speed_limits = (speed_limits[:-1] + speed_limits[1:]) / 2.0
    baseline_time_s = float(np.sum(ds / np.maximum(seg_speed_limits, 0.1)))
    time_budget_s = baseline_time_s * time_budget_fraction

    print(f"  Solving NLP: {n_steps} steps at {spatial_step_m:.0f}m resolution...", flush=True)

    opt_speeds = _solve_nlp(
        n_steps=n_steps,
        ds=ds,
        grades=grades,
        constraints=constraints,
        vehicle=vehicle,
        time_budget_s=time_budget_s,
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
    time_budget_s: float,
    verbose: bool,
) -> np.ndarray:
    """
    Build and solve the CasADi NLP using the w = v² substitution.

    Substituting w[i] = v[i]² makes ALL force terms linear in w. The travel
    time constraint sum(ds/sqrt(w_mid)) <= T is encoded without any sqrt via
    the epigraph form: t[i]^2 * w_mid >= ds^2, sum(t) <= T. This eliminates
    the NaN-in-sqrt issue when IPOPT explores w near zero during barrier steps.

    Returns the optimal speed array (m/s) at the n_steps spatial points.
    """
    opti = ca.Opti()

    # Decision variables: w[i] = v[i]² (squared speeds, m²/s²)
    w = opti.variable(n_steps)

    # Auxiliary variables: engine work per segment (non-negative)
    p = opti.variable(n_steps - 1)

    # Auxiliary variables: segment travel times (avoids sqrt in time constraint).
    # The travel time for segment i is t[i] = ds / v_mid = ds / sqrt(w_mid).
    # Instead of encoding this as sum(ds/sqrt(w_mid)) <= T, we use the
    # equivalent epigraph form:  t[i]^2 * w_mid >= ds^2  (for t[i] >= 0).
    # This is a smooth quadratic constraint — no sqrt, no NaN.
    t = opti.variable(n_steps - 1)

    # Vehicle constants
    m   = vehicle.mass_kg
    Cd  = vehicle.drag_coefficient
    A   = vehicle.frontal_area_m2
    Crr = vehicle.rolling_resistance

    seg_speed_limits = (constraints.speed_upper_ms[:-1] + constraints.speed_upper_ms[1:]) / 2.0

    for i in range(1, n_steps):
        w_mid = (w[i] + w[i - 1]) / 2.0
        g_mid = (grades[i] + grades[i - 1]) / 2.0

        # Forces (all linear in w)
        f_aero    = 0.5 * RHO_AIR * Cd * A * w_mid
        f_roll    = Crr * m * G
        f_grade   = m * G * g_mid
        f_inertia = m * (w[i] - w[i - 1]) / (2.0 * ds)

        work_i = (f_aero + f_roll + f_grade + f_inertia) * ds

        # p[i-1] = max(work_i, 0)
        opti.subject_to(p[i - 1] >= work_i)
        opti.subject_to(p[i - 1] >= 0)

        # t[i-1] >= ds / sqrt(w_mid) encoded as t[i-1]^2 * w_mid >= ds^2
        opti.subject_to(t[i - 1] >= 0)
        opti.subject_to(t[i - 1] ** 2 * w_mid >= ds ** 2)

    # Objective: minimize total propulsive work
    opti.minimize(ca.sum1(p))

    # Travel time budget: sum of segment times <= T_budget
    opti.subject_to(ca.sum1(t) <= time_budget_s)

    # Speed (squared) bounds
    w_lower = constraints.speed_lower_ms ** 2
    w_upper = constraints.speed_upper_ms ** 2
    for i in range(n_steps):
        opti.subject_to(w[i] >= w_lower[i])
        opti.subject_to(w[i] <= w_upper[i])

    # Acceleration / deceleration: (w[i]-w[i-1])/(2*ds) in [-a_max, a_max]
    for i in range(1, n_steps):
        dw = (w[i] - w[i - 1]) / (2.0 * ds)
        opti.subject_to(dw <=  constraints.max_accel_ms2)
        opti.subject_to(dw >= -constraints.max_decel_ms2)

    # Warm start
    opti.set_initial(w, constraints.speed_upper_ms ** 2)
    opti.set_initial(p, np.zeros(n_steps - 1))
    t_init = ds / np.maximum(seg_speed_limits, 0.1)
    opti.set_initial(t, t_init)

    solver_opts = {
        "ipopt.print_level":            5 if verbose else 0,
        "ipopt.max_iter":               3000,
        "ipopt.tol":                    1e-5,
        "ipopt.acceptable_tol":         1e-4,
        "ipopt.acceptable_iter":        10,
        "ipopt.mu_strategy":            "adaptive",
        "ipopt.hessian_approximation":  "limited-memory",
        "print_time":                   1 if verbose else 0,
    }
    opti.solver("ipopt", solver_opts)

    try:
        sol = opti.solve()
        w_opt = sol.value(w)
        converged = True
    except RuntimeError as e:
        print(f"  Optimizer warning: {e}", flush=True)
        print("  Using best solution found so far.", flush=True)
        w_opt = opti.debug.value(w)
        converged = False

    if converged:
        print("  Converged successfully.", flush=True)

    # Convert w back to v, clamp to speed bounds
    speeds = np.sqrt(np.maximum(w_opt, 0.0))
    speeds = np.clip(speeds, constraints.speed_lower_ms, constraints.speed_upper_ms)
    return speeds
