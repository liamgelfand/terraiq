"""
Batch simulation runner — tests the optimizer across multiple diverse routes.

Runs baseline + optimized simulation for every route in ROUTES, saves a
comparison plot per route, and prints a summary table at the end.
Results are also saved to batch_results.csv for further analysis.

Usage:
    python -u run_batch.py

Expected runtime: ~3–5 minutes per route (elevation API + optimizer).
Total: ~20–30 minutes for all 5 routes.
"""

import sys
import csv
import time
from pathlib import Path

sys.path.insert(0, ".")

from simulation.runner import SimulationRunner
from simulation.evaluator import EvaluationReport
from visualization.plotter import plot_comparison
from data.vehicle_profiles.freightliner_2022 import Freightliner2022

# ── Route definitions ─────────────────────────────────────────────────────────
#
# Routes are chosen to cover a range of terrain types:
#   - Mountain (heavy grade)  → expect high savings
#   - Rolling hills           → expect moderate savings
#   - Flat highway            → expect low savings (validates model)
#
ROUTES = [
    {
        "name":        "Donner Pass → Sacramento",
        "origin":      (39.30, -120.14),   # Truckee, CA
        "destination": (38.73, -121.38),   # Sacramento, CA
        "terrain":     "Mountain descent",
    },
    {
        "name":        "Denver → Grand Junction",
        "origin":      (39.74, -104.98),   # Denver, CO
        "destination": (39.07, -108.55),   # Grand Junction, CO
        "terrain":     "Rocky Mountain grades",
    },
    {
        "name":        "Provo → St. George",
        "origin":      (40.23, -111.66),   # Provo, UT
        "destination": (37.10, -113.58),   # St. George, UT
        "terrain":     "Desert rolling",
    },
    {
        "name":        "Asheville → Charlotte",
        "origin":      (35.57, -82.55),    # Asheville, NC
        "destination": (35.23, -80.84),    # Charlotte, NC
        "terrain":     "Appalachian grades",
    },
    {
        "name":        "Nashville → Memphis",
        "origin":      (36.17, -86.78),    # Nashville, TN
        "destination": (35.15, -90.05),    # Memphis, TN
        "terrain":     "Flat highway",
    },
]

SPATIAL_STEP_M = 100.0
OUTPUT_DIR     = Path("batch_outputs")

# ──────────────────────────────────────────────────────────────────────────────

def run_batch():
    OUTPUT_DIR.mkdir(exist_ok=True)
    vehicle = Freightliner2022()
    results = []

    print("\n" + "="*70)
    print("  TERRAIQ BATCH SIMULATION")
    print(f"  Vehicle: {vehicle.name}")
    print(f"  Routes:  {len(ROUTES)}")
    print(f"  Outputs: {OUTPUT_DIR}/")
    print("="*70 + "\n")

    for i, route in enumerate(ROUTES, 1):
        print(f"\n[{i}/{len(ROUTES)}] {route['name']}  ({route['terrain']})")
        print("-" * 60)

        runner = SimulationRunner(vehicle=vehicle)
        t_start = time.time()

        try:
            baseline = runner.run(
                origin=route["origin"],
                destination=route["destination"],
                route_name=route["name"],
            )

            optimized = runner.run_optimized(
                origin=route["origin"],
                destination=route["destination"],
                route_name=route["name"],
                spatial_step_m=SPATIAL_STEP_M,
            )

            report = EvaluationReport(baseline=baseline, optimized=optimized)

            # Save comparison plot
            plot_name = route["name"].replace(" ", "_").replace("→", "to") + ".png"
            plot_path = OUTPUT_DIR / plot_name
            plot_comparison(report, save_path=plot_path, show=False)

            results.append({
                "route":          route["name"],
                "terrain":        route["terrain"],
                "distance_km":    f"{baseline.total_distance_km:.1f}",
                "elev_gain_m":    f"{baseline.elevation_gain_m:.0f}",
                "baseline_L":     f"{baseline.total_fuel_liters:.2f}",
                "optimized_L":    f"{optimized.total_fuel_liters:.2f}",
                "saved_L":        f"{report.fuel_saved_liters:.2f}",
                "saved_pct":      f"{report.fuel_saved_pct:.1f}",
                "co2_saved_kg":   f"{report.co2_saved_kg:.1f}",
                "status":         "OK",
            })

            elapsed = time.time() - t_start
            print(f"  ✓ Done in {elapsed:.0f}s — saved {report.fuel_saved_liters:.2f} L ({report.fuel_saved_pct:.1f}%)", flush=True)

        except Exception as e:
            print(f"  ✗ FAILED: {e}", flush=True)
            results.append({
                "route":     route["name"],
                "terrain":   route["terrain"],
                "status":    f"FAILED: {e}",
                "distance_km": "-", "elev_gain_m": "-",
                "baseline_L": "-", "optimized_L": "-",
                "saved_L": "-", "saved_pct": "-", "co2_saved_kg": "-",
            })

    _print_summary_table(results)
    _save_csv(results)


def _print_summary_table(results: list[dict]):
    print("\n\n" + "="*90)
    print("  BATCH RESULTS SUMMARY")
    print("="*90)
    print(f"  {'Route':<35} {'Terrain':<22} {'km':>6} {'Base':>7} {'Opt':>7} {'Saved':>7} {'%':>6}")
    print("-"*90)
    for r in results:
        if r["status"] != "OK":
            print(f"  {r['route']:<35} {r['terrain']:<22}  FAILED")
            continue
        print(
            f"  {r['route']:<35} {r['terrain']:<22} "
            f"{r['distance_km']:>6} "
            f"{r['baseline_L']:>6}L "
            f"{r['optimized_L']:>6}L "
            f"{r['saved_L']:>6}L "
            f"{r['saved_pct']:>5}%"
        )

    ok = [r for r in results if r["status"] == "OK"]
    if ok:
        avg_pct = sum(float(r["saved_pct"]) for r in ok) / len(ok)
        total_saved = sum(float(r["saved_L"]) for r in ok)
        print("-"*90)
        print(f"  {'Average savings:':<58} {avg_pct:>5.1f}%")
        print(f"  {'Total fuel saved across all routes:':<58} {total_saved:>5.2f} L")
    print("="*90 + "\n")


def _save_csv(results: list[dict]):
    csv_path = OUTPUT_DIR / "batch_results.csv"
    fieldnames = [
        "route", "terrain", "distance_km", "elev_gain_m",
        "baseline_L", "optimized_L", "saved_L", "saved_pct", "co2_saved_kg", "status",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"Results saved to {csv_path}")


if __name__ == "__main__":
    run_batch()
