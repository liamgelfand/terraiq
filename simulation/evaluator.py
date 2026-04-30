"""
Evaluator: comparison metrics between two simulation results.

Compares a baseline run against an optimized run and produces
a structured report with fuel savings, efficiency gains, and
per-segment breakdowns.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from simulation.runner import SimulationResult

# US average retail diesel — used as the default cost basis.
# 1 US gallon = 3.78541 L; $3.90/gal ≈ $1.03/L (EIA, early 2026)
DIESEL_PRICE_PER_LITER_USD: float = 1.03


@dataclass
class EvaluationReport:
    baseline: SimulationResult
    optimized: SimulationResult
    diesel_price_per_liter: float = DIESEL_PRICE_PER_LITER_USD

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
        # Diesel combustion: ~2.68 kg CO₂ per litre (IPCC/EIA)
        return self.fuel_saved_liters * 2.68

    @property
    def cost_saved_usd(self) -> float:
        return self.fuel_saved_liters * self.diesel_price_per_liter

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
        print(f"  Cost saved:      ${self.cost_saved_usd:.2f}  "
              f"(@ ${self.diesel_price_per_liter:.2f}/L)")
        print(f"  CO₂ saved:       {self.co2_saved_kg:.1f} kg")
        print("="*60)
        print()
