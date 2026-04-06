"""
Run a baseline simulation and display results.

Usage:
    python run_simulation.py

Edit the ORIGIN, DESTINATION, and ROUTE_NAME variables below to change the route.
Coordinates are (latitude, longitude).
"""

import sys
sys.path.insert(0, ".")

from simulation.runner import SimulationRunner
from visualization.plotter import plot_baseline
from data.vehicle_profiles.freightliner_2022 import Freightliner2022

# ── Route Configuration ────────────────────────────────────────────────────────

ROUTE_NAME = "Donner Pass — Sacramento"
ORIGIN      = (39.30, -120.14)   # Truckee, CA (east side of Donner Pass)
DESTINATION = (38.73, -121.38)   # Sacramento, CA

# Optional: set a fixed speed (m/s) instead of following speed limits.
# e.g. 24.4 = 88 km/h constant. Set to None to follow speed limits.
TARGET_SPEED_MS = None

# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    runner = SimulationRunner(vehicle=Freightliner2022())

    result = runner.run(
        origin=ORIGIN,
        destination=DESTINATION,
        route_name=ROUTE_NAME,
        target_speed_ms=TARGET_SPEED_MS,
    )

    result.print_summary()
    plot_baseline(result, save_path="simulation_output.png")
