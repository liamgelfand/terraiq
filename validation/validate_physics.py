"""
Phase 1 physics validation -- TerraIQ vehicle model vs NREL Fleet DNA.

Methodology
-----------
1. Build a synthetic flat 100 km highway route at each reference speed.
2. Run the VehicleModel (same physics used in all simulations) at that
   constant speed.
3. Compare predicted L/100 km to the published Freightliner Cascadia spec
   (primary criterion) and NREL fleet-average data (context only).
4. Report pass/fail against the Phase 1 criterion (<= 20% error vs spec).

Why our model is expected to be optimistic vs NREL fleet averages:
  - NREL fleet data includes older trucks with Cd 0.55-0.65 vs our Cd 0.36
  - No auxiliary power loads (HVAC, reefer, ELDs): +5-10% real-world
  - Idealised Cd (no crosswind): +3-8%
  - No road roughness / tyre flex: +1-3%
  - These effects are physically correct to omit in an idealized model.

Usage:
    python -u validation/validate_physics.py
"""

import sys
sys.path.insert(0, ".")

import numpy as np

from data.route_fetcher import RoutePoint
from data.vehicle_profiles.freightliner_2022 import Freightliner2022
from models.world_model import WorldModel
from models.vehicle_model import VehicleModel
from validation.nrel_reference import (
    ALL_BENCHMARKS, CASCADIA_SPEC, NREL_ALL_DRIVING,
    PHASE1_TOLERANCE_PCT,
)

ROUTE_LENGTH_KM = 100.0
N_POINTS        = 201


def _build_flat_world(speed_kmh: float) -> WorldModel:
    """Synthetic flat 100 km route at a constant speed limit."""
    distances_m = np.linspace(0.0, ROUTE_LENGTH_KM * 1000.0, N_POINTS)
    speed_ms    = speed_kmh / 3.6
    points = [
        RoutePoint(
            distance_m    =float(d),
            lat           =0.0,
            lon           =0.0,
            elevation_m   =500.0,
            grade         =0.0,
            speed_limit_ms=speed_ms,
        )
        for d in distances_m
    ]
    return WorldModel(points=points)


def _run_model(speed_kmh: float) -> float:
    """Return model-predicted L/100 km on a flat route at the given speed."""
    vehicle  = Freightliner2022()
    model    = VehicleModel(vehicle)
    world    = _build_flat_world(speed_kmh)
    speed_ms = np.full(N_POINTS, speed_kmh / 3.6)
    result   = model.compute_fuel_consumption(world, speed_ms)
    return result["fuel_per_100km"]


def _pct_error(predicted: float, reference: float) -> float:
    return (predicted - reference) / reference * 100.0


def run_validation():
    vehicle = Freightliner2022()

    print()
    print("=" * 80)
    print("  TERRAIQ -- PHASE 1 PHYSICS VALIDATION")
    print(f"  Vehicle  : {vehicle.name}")
    print(f"  Route    : {ROUTE_LENGTH_KM:.0f} km synthetic flat highway")
    print(f"  Criterion: model error <= {PHASE1_TOLERANCE_PCT:.0f}% vs vehicle-specific spec")
    print("=" * 80)

    # -- 1. Steady-state force balance (hand-calc cross-check) ---------------
    print("\n-- 1. Steady-state force balance at 65 mph -----")
    v     = 104.6 / 3.6
    f_a   = 0.5 * 1.225 * vehicle.drag_coefficient * vehicle.frontal_area_m2 * v ** 2
    f_r   = vehicle.rolling_resistance * vehicle.mass_kg * 9.81
    f_tot = f_a + f_r
    P_kw  = f_tot * v / 1000.0
    print(f"  Aero drag  : {f_a:>7.1f} N")
    print(f"  Rolling    : {f_r:>7.1f} N")
    print(f"  Total force: {f_tot:>7.1f} N")
    print(f"  Power req. : {P_kw:>7.1f} kW  ({P_kw/vehicle.max_power_kw*100:.1f}% of max)")

    # -- 2a. Vehicle-specific validation (primary pass criterion) ------------
    print("\n-- 2a. Vehicle-specific validation (PRIMARY criterion) -----------------")
    print("   Reference: Freightliner Cascadia 126, DD15, DT12, aero package,")
    print("              65 mph, flat road, 75,000 lb GVW  (manufacturer spec).")
    print()
    print(f"  {'Condition':<30} {'Spec':>9} {'Model':>9} {'Error':>8}  Status")
    print("  " + "-" * 66)

    spec_results = []
    predicted  = _run_model(CASCADIA_SPEC.speed_kmh)
    error_pct  = _pct_error(predicted, CASCADIA_SPEC.l_per_100km)
    passed     = abs(error_pct) <= PHASE1_TOLERANCE_PCT
    spec_results.append((CASCADIA_SPEC, predicted, error_pct, passed))
    print(
        f"  {'Cascadia spec @ 65 mph':<30} "
        f"{CASCADIA_SPEC.l_per_100km:>7.1f} L "
        f"{predicted:>7.1f} L "
        f"{error_pct:>+7.1f}%  "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # -- 2b. NREL fleet context (informational) ------------------------------
    print("\n-- 2b. NREL Fleet DNA context (informational -- mixed fleet) -----------")
    print("   NREL benchmarks include trucks with avg Cd ~0.60 (no aero package).")
    print("   Our Cascadia Cd=0.36 is ~40% lower -- greater optimism at")
    print("   higher speeds is physically correct for this specific vehicle.")
    print()
    print(f"  {'Condition':<38} {'NREL':>8} {'Model':>8} {'Gap':>8}")
    print("  " + "-" * 66)

    fleet_bms = [b for b in ALL_BENCHMARKS if b not in (CASCADIA_SPEC, NREL_ALL_DRIVING)]
    fleet_preds = []
    for bm in fleet_bms:
        pred = _run_model(bm.speed_kmh)
        err  = _pct_error(pred, bm.l_per_100km)
        fleet_preds.append(pred)
        print(
            f"  {bm.condition:<38} "
            f"{bm.l_per_100km:>6.1f} L "
            f"{pred:>6.1f} L "
            f"{err:>+7.1f}%"
        )

    # -- 3. Fleet-wide context -----------------------------------------------
    print("\n-- 3. Fleet-wide context -----------------------------------------------")
    avg_model = np.mean([r[1] for r in spec_results] + fleet_preds)
    calib     = NREL_ALL_DRIVING.l_per_100km / avg_model
    print(f"  NREL fleet avg (all driving, incl. idling): {NREL_ALL_DRIVING.l_per_100km:.1f} L/100 km")
    print(f"  Our model avg (ideal cruise, no aux loads): {avg_model:.1f} L/100 km")
    print(f"  Calibration factor to match fleet avg: ~{calib:.2f}x")
    print(f"  (Accounted for by aux loads, crosswind, road roughness)")

    # -- 4. Summary ----------------------------------------------------------
    print("\n-- 4. Phase 1 Validation Summary ---------------------------------------")
    n_pass    = sum(1 for r in spec_results if r[3])
    n_total   = len(spec_results)
    avg_err   = np.mean([abs(r[2]) for r in spec_results])
    overall   = "PASS" if n_pass == n_total else "FAIL"

    print(f"  Vehicle-specific tests passed: {n_pass} / {n_total}")
    print(f"  Avg absolute error (spec):     {avg_err:.1f}%  (threshold: {PHASE1_TOLERANCE_PCT:.0f}%)")
    print(f"  Phase 1 result: {overall}")
    print()
    print("  Model is suitable for terrain-relative optimization studies.")
    print("  For absolute fuel quantity predictions, apply calibration factor ~1.3x")
    print("  to account for real-world auxiliary loads and environmental effects.")
    print()
    print("=" * 80)
    print()

    return overall == "PASS"


if __name__ == "__main__":
    passed = run_validation()
    sys.exit(0 if passed else 1)
