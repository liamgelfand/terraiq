"""
Evaluator: comparison metrics between two simulation results.

Compares a baseline run against an optimized run and produces
a structured report with fuel savings, efficiency gains, and
per-segment breakdowns.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simulation.runner import SimulationResult


@dataclass
class EvaluationReport:
    baseline: SimulationResult
    optimized: SimulationResult

    @property
    def fuel_saved_liters(self) -> float:
        return self.baseline.total_fuel_liters - self.optimized.total_fuel_liters

    @property
    def fuel_saved_pct(self) -> float:
        if self.baseline.total_fuel_liters == 0:
            return 0.0
        return (self.fuel_saved_liters / self.baseline.total_fuel_liters) * 100.0

    @property
    def co2_saved_kg(self) -> float:
        return self.fuel_saved_liters * 2.68

    def print_report(self):
        print("\n" + "="*60)
        print("  OPTIMIZATION RESULTS")
        print("="*60)
        print(f"  Route:           {self.baseline.route_name}")
        print(f"  Vehicle:         {self.baseline.vehicle_name}")
        print(f"  Distance:        {self.baseline.total_distance_km:.1f} km")
        print("-"*60)
        print(f"  Baseline fuel:   {self.baseline.total_fuel_liters:.2f} L  "
              f"({self.baseline.fuel_per_100km:.2f} L/100km)")
        print(f"  Optimized fuel:  {self.optimized.total_fuel_liters:.2f} L  "
              f"({self.optimized.fuel_per_100km:.2f} L/100km)")
        print("-"*60)
        print(f"  Fuel saved:      {self.fuel_saved_liters:.2f} L  "
              f"({self.fuel_saved_pct:.1f}%)")
        print(f"  CO2 saved:       {self.co2_saved_kg:.1f} kg")
        print("="*60)
        print()
