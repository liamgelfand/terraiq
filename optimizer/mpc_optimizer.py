"""
Fuel-optimal speed trajectory optimizer.

Decision variable: v[i]  (speed in m/s at spatial step i)

Using v directly (not w = v²):
  - Travel time per segment = ds / v_mid  →  exact, convex, no sqrt needed
  - v_min > 0 is a hard lower bound, so v_mid > 0 always → no NaN ever
  - Aero force = 0.5·ρ·Cd·A·v_mid²  →  quadratic; exact Hessian handles it
  - Inertia    = m·(v[i]²−v[i-1]²)/(2·ds) → also quadratic in v

Formulation
-----------
    minimize    Σ bsfc(P_norm[i]) · p[i] / 3.6e6        (fuel mass, grams)
    subject to  p[i] ≥ (F_aero + F_roll + F_grade + F_inertia)·ds  [work constraint]
                p[i] ≥ 0
                Σ ds/v_mid[i] ≤ T_budget                [travel time — exact, convex]
                v_min ≤ v[i] ≤ speed_limit[i]
                |Δv²[i]| / (2·ds) ≤ a_max               [kinematic accel/decel]

where:
  p[i]     = propulsive work per segment (J) = max(F_net·ds, 0)
  P_norm[i] = p[i]·v_mid[i] / (ds · P_max_W)   (normalised engine power 0–1)
  bsfc(x)  = a0 + a1·x + a2·x²  (g/kWh, quadratic fit of BSFC map at highway RPM)

Using BSFC instead of raw work correctly penalises light-load conditions
(BSFC ≈ 290 g/kWh at 10% load) versus the efficient sweet spot
(BSFC ≈ 188 g/kWh at 70% load for the Detroit DD15).  The derivative
d(bsfc·p)/d(p) > 0 for all p ≥ 0, so the constraint p[i] ≥ max(work,0)
still binds at the optimum — the min-fuel solution equals the min-work
solution structurally, but the objective landscape better reflects real
engine efficiency.
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


def _fit_bsfc_polynomial(vehicle: VehicleProfile) -> tuple[float, float, float]:
    """
    Fit a quadratic BSFC(P_norm) polynomial for highway operating conditions.

    Extracts the BSFC-vs-load curve at the representative highway RPM
    (top gear at 25 m/s on flat terrain) and fits a least-squares quadratic.

    Returns:
        (a0, a1, a2) such that BSFC ≈ a0 + a1·P_norm + a2·P_norm²  [g/kWh]
        where P_norm = engine_power / max_power  (0–1)
    """
    import math as _math

    bsfc_map = vehicle.get_bsfc_map()

    # Representative highway operating point: top gear at 25 m/s, flat road
    v_rep = 25.0  # m/s (~90 km/h)
    gear_idx = vehicle.get_gear(v_rep, 0.0)
    gear_ratio = vehicle.gear_ratios[gear_idx]
    rpm_rep = (
        v_rep / vehicle.wheel_radius_m
        * gear_ratio
        * vehicle.final_drive_ratio
        * 60.0
        / (2.0 * _math.pi)
    )
    rpm_rep = float(np.clip(rpm_rep, bsfc_map.rpm_points[0], bsfc_map.rpm_points[-1]))

    # Sample BSFC at this RPM across the full load range
    loads = bsfc_map.load_points
    bsfc_vals = bsfc_map.lookup_array(np.full_like(loads, rpm_rep), loads)

    # Least-squares quadratic fit: bsfc ≈ a0 + a1*load + a2*load²
    # np.polyfit returns highest-degree coeff first: [a2, a1, a0]
    a2, a1, a0 = np.polyfit(loads, bsfc_vals, deg=2)
    return float(a0), float(a1), float(a2)


def optimize_full_route(
    world: WorldModel,
    vehicle: VehicleProfile,
    spatial_step_m: float = DEFAULT_SPATIAL_STEP_M,
    time_budget_fraction: float = 1.02,
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
                              (1.02 = arrive no more than 2% later than driving
                              at speed limits). Prevents the optimizer from
                              slowing down everywhere just to reduce aero drag.
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

    # Auto-scale: cap at 500 steps. Exact-Hessian IPOPT is much faster per iteration
    # than L-BFGS but each iteration costs more, so a smaller problem converges faster.
    # At 500 steps, a 400km route uses 800m spacing — still captures terrain well.
    MAX_STEPS = 500
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

    # Baseline travel time using the CAPPED speed limits (min of road limit and
    # vehicle max speed). The optimizer cannot exceed vehicle max speed regardless
    # of the road limit, so using raw OSM limits here would set an unreachable
    # baseline and make the time budget infeasible on routes with limits > vehicle max.
    capped_seg_speeds = (constraints.speed_upper_ms[:-1] + constraints.speed_upper_ms[1:]) / 2.0
    baseline_time_s = float(np.sum(ds / np.maximum(capped_seg_speeds, 0.1)))
    time_budget_s = baseline_time_s * time_budget_fraction

    # Fit BSFC polynomial once per call (fast — pure numpy)
    bsfc_poly = _fit_bsfc_polynomial(vehicle)

    print(f"  Solving NLP: {n_steps} steps at {spatial_step_m:.0f}m resolution...", flush=True)

    opt_speeds = _solve_lp(
        n_steps=n_steps,
        ds=ds,
        grades=grades,
        constraints=constraints,
        vehicle=vehicle,
        time_budget_s=time_budget_s,
        bsfc_poly=bsfc_poly,
        verbose=verbose,
    )

    # Interpolate back onto the original world model distance grid
    return np.interp(world.distance_m, distances, opt_speeds)


def _solve_lp(
    n_steps: int,
    ds: float,
    grades: np.ndarray,
    constraints,
    vehicle: VehicleProfile,
    time_budget_s: float,
    bsfc_poly: tuple[float, float, float],
    verbose: bool,
) -> np.ndarray:
    """
    Solve the NLP for fuel-optimal speed trajectory.

    Uses v (speed, m/s) directly as decision variable. The travel time
    constraint ds/v_mid is exact and convex. v_min > 0 ensures v_mid > 0
    always, so no NaN can occur during IPOPT's barrier iterations.

    The objective minimises total fuel mass (grams), using a quadratic BSFC
    polynomial to correctly penalise light-load (low-efficiency) operation.

    Returns the optimal speed array (m/s) at the n_steps spatial points.
    """
    opti = ca.Opti()

    # Decision variables
    v = opti.variable(n_steps)        # speed at each spatial step (m/s)
    p = opti.variable(n_steps - 1)   # non-negative engine work per segment (J)

    # Vehicle constants
    m       = vehicle.mass_kg
    Cd      = vehicle.drag_coefficient
    A       = vehicle.frontal_area_m2
    Crr     = vehicle.rolling_resistance
    P_max_W = vehicle.max_power_kw * 1000.0   # peak engine power (W)

    # BSFC polynomial coefficients: bsfc [g/kWh] = a0 + a1*P_norm + a2*P_norm^2
    # P_norm = p[i]*v_mid / (ds * P_max_W)  — normalised engine power (0–1)
    a0, a1, a2 = bsfc_poly

    # Build per-segment constraints and fuel objective
    travel_time = 0.0
    total_fuel_g = 0.0
    for i in range(1, n_steps):
        v_mid = (v[i] + v[i - 1]) / 2.0
        g_mid = (grades[i] + grades[i - 1]) / 2.0

        # Longitudinal force model
        f_aero    = 0.5 * RHO_AIR * Cd * A * v_mid ** 2    # quadratic in v
        f_roll    = Crr * m * G
        f_grade   = m * G * g_mid
        f_inertia = m * (v[i] ** 2 - v[i - 1] ** 2) / (2.0 * ds)  # quadratic in v

        work_i = (f_aero + f_roll + f_grade + f_inertia) * ds

        # p[i-1] = max(work_i, 0): LP max reformulation via two linear constraints
        opti.subject_to(p[i - 1] >= work_i)
        opti.subject_to(p[i - 1] >= 0)

        # Exact travel time: ds / v_mid (convex in v; no sqrt because v is the variable)
        travel_time = travel_time + ds / v_mid

        # BSFC-weighted fuel mass for this segment (grams)
        # P_norm = propulsive power / max_power = (p[i-1]/ds * v_mid) / P_max_W
        P_norm_i = p[i - 1] * v_mid / (ds * P_max_W)
        bsfc_i   = a0 + a1 * P_norm_i + a2 * P_norm_i ** 2   # g/kWh
        # fuel [g] = bsfc [g/kWh] * work [J] / (1000 W/kW * 3600 s/h)
        total_fuel_g = total_fuel_g + bsfc_i * p[i - 1] / 3.6e6

    # Objective: minimise total fuel consumed (grams)
    opti.minimize(total_fuel_g)

    # Travel time budget: exact constraint, no approximation
    opti.subject_to(travel_time <= time_budget_s)

    # Speed bounds
    for i in range(n_steps):
        opti.subject_to(v[i] >= constraints.speed_lower_ms[i])
        opti.subject_to(v[i] <= constraints.speed_upper_ms[i])

    # Kinematic acceleration / deceleration
    for i in range(1, n_steps):
        accel = (v[i] ** 2 - v[i - 1] ** 2) / (2.0 * ds)
        opti.subject_to(accel <=  constraints.max_accel_ms2)
        opti.subject_to(accel >= -constraints.max_decel_ms2)

    # Warm start: v at speed limits; p at actual work values at those speeds.
    # Initialising p=0 violates p[i]>=work_i by ~2-3 MJ per segment for a loaded
    # truck at highway speeds — a ~1 GJ total violation IPOPT cannot restore from.
    # Setting p to the exact work at the warm-start speed makes the start fully
    # feasible for every constraint simultaneously.
    v_init = constraints.speed_upper_ms.copy()
    p_init = np.empty(n_steps - 1)
    for i in range(1, n_steps):
        v_mid_i = (v_init[i] + v_init[i - 1]) / 2.0
        g_mid_i = (grades[i] + grades[i - 1]) / 2.0
        f_a = 0.5 * RHO_AIR * Cd * A * v_mid_i ** 2
        f_r = Crr * m * G
        f_g = m * G * g_mid_i
        f_i = m * (v_init[i] ** 2 - v_init[i - 1] ** 2) / (2.0 * ds)
        p_init[i - 1] = max((f_a + f_r + f_g + f_i) * ds, 0.0)
    opti.set_initial(v, v_init)
    opti.set_initial(p, p_init)

    solver_opts = {
        "ipopt.print_level":        5 if verbose else 0,
        "ipopt.max_iter":           1000,
        "ipopt.tol":                1e-6,
        "ipopt.acceptable_tol":     1e-5,
        "ipopt.acceptable_iter":    5,
        "ipopt.mu_strategy":        "adaptive",
        "ipopt.nlp_scaling_method": "gradient-based",
        "ipopt.bound_push":         1e-4,   # keeps v away from bounds → no NaN
        "ipopt.bound_frac":         1e-4,
        "print_time":               1 if verbose else 0,
    }
    opti.solver("ipopt", solver_opts)

    try:
        sol = opti.solve()
        v_opt = sol.value(v)
        print("  Converged successfully.", flush=True)
    except RuntimeError as e:
        print(f"  Optimizer warning: {e}", flush=True)
        print("  Using best solution found so far.", flush=True)
        v_opt = opti.debug.value(v)

    return np.clip(v_opt, constraints.speed_lower_ms, constraints.speed_upper_ms)
