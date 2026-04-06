"""
Run baseline and optimized simulations and compare results.

Usage:
    python -u run_simulation.py

Edit the configuration section below to change the route or vehicle.
Coordinates are (latitude, longitude).
"""

import sys
sys.path.insert(0, ".")

from simulation.runner import SimulationRunner
from simulation.evaluator import EvaluationReport
from visualization.plotter import plot_baseline, plot_comparison
from data.vehicle_profiles.freightliner_2022 import Freightliner2022

# ── Configuration ──────────────────────────────────────────────────────────────

ROUTE_NAME  = "Donner Pass — Sacramento"
ORIGIN      = (39.30, -120.14)   # Truckee, CA
DESTINATION = (38.73, -121.38)   # Sacramento, CA

# Optimizer spatial step — smaller = more accurate but slower solver
# 100m is a good balance for a first run
SPATIAL_STEP_M = 100.0

# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    runner = SimulationRunner(vehicle=Freightliner2022())

    # Run baseline — route fetch happens here and is cached
    baseline = runner.run(
        origin=ORIGIN,
        destination=DESTINATION,
        route_name=ROUTE_NAME,
    )
    baseline.print_summary()

    # Run optimizer — reuses cached route, no second network fetch
    optimized = runner.run_optimized(
        origin=ORIGIN,
        destination=DESTINATION,
        route_name=ROUTE_NAME,
        spatial_step_m=SPATIAL_STEP_M,
    )
    optimized.print_summary()

    # Print comparison
    report = EvaluationReport(baseline=baseline, optimized=optimized)
    report.print_report()

    # Save plots
    plot_baseline(baseline, save_path="baseline_output.png", show=False)
    plot_comparison(report, save_path="comparison_output.png", show=False)
    print("Plots saved: baseline_output.png, comparison_output.png")
