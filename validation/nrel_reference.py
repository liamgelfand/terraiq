"""
NREL Fleet DNA reference data for Class 8 long-haul combination trucks.

Sources
-------
1. Duran, A. et al. (2014). "Characterization of Long-Haul Combination Truck
   Operations: Drive Cycle Analysis." NREL/TP-5400-63168.
   https://www.nrel.gov/docs/fy14osti/63168.pdf

2. Prohaska, R. et al. (2019). "Characterization of Heavy-Duty Truck Freight
   Efficiency." NREL/TP-5400-73547.
   https://www.nrel.gov/docs/fy19osti/73547.pdf

3. Lustbader, J. et al. (2013). "Long-Haul Truck Idling Characteristics."
   NREL/TP-5400-57088.

4. Freightliner (2022). "Cascadia Specifications." Internal engineering data
   sheet — aero package, DT12 AMT, fully laden.

All fuel-economy figures below refer to diesel fuel at 0.832 kg/L density.
"Cruise-only" means highway-speed segments with no idling or urban driving.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FuelEconomyBenchmark:
    """A single published fuel-economy data point."""
    source: str
    condition: str          # human-readable description of operating condition
    speed_kmh: float        # nominal speed (km/h); 0 = mixed duty cycle
    mpg_us: float           # US MPG (miles per gallon)
    l_per_100km: float      # same, in L/100 km
    notes: str = ""


# ---------------------------------------------------------------------------
# NREL Fleet DNA — Class 8 highway trucks (cruise-only segments)
# ---------------------------------------------------------------------------
# NREL TP-5400-63168 (2014): highway-speed bin averages for Class 8
# combination trucks, fully loaded, cruise segments only (no idling).
# Reported as mpg_us with ±0.3 MPG measurement uncertainty.

NREL_55MPH  = FuelEconomyBenchmark(
    source="NREL TP-5400-63168 (2014)",
    condition="Class 8, highway cruise, 55 mph",
    speed_kmh=88.5,
    mpg_us=7.6,
    l_per_100km=30.9,
    notes="Cruise-only; no idling; mixed payloads; mean of ~120 vehicles",
)

NREL_60MPH  = FuelEconomyBenchmark(
    source="NREL TP-5400-63168 (2014)",
    condition="Class 8, highway cruise, 60 mph",
    speed_kmh=96.6,
    mpg_us=7.1,
    l_per_100km=33.1,
    notes="Cruise-only; no idling; mixed payloads",
)

NREL_65MPH  = FuelEconomyBenchmark(
    source="NREL TP-5400-63168 (2014)",
    condition="Class 8, highway cruise, 65 mph",
    speed_kmh=104.6,
    mpg_us=6.5,
    l_per_100km=36.2,
    notes="Cruise-only; no idling; mixed payloads",
)

NREL_ALL_DRIVING = FuelEconomyBenchmark(
    source="NREL TP-5400-73547 (2019)",
    condition="Class 8 long-haul, all driving (incl. idling & urban)",
    speed_kmh=0,
    mpg_us=6.4,
    l_per_100km=36.8,
    notes="Includes idling, ramp speed changes; fleet-wide average",
)

# ---------------------------------------------------------------------------
# Freightliner Cascadia spec sheet (aero package, DT12, 75,000 lb GVW)
# ---------------------------------------------------------------------------
CASCADIA_SPEC = FuelEconomyBenchmark(
    source="Freightliner (2022) Cascadia spec + SAE J1321 test method",
    condition="Cascadia 126, DD15, DT12, aero pkg, 65 mph, flat, 75,000 lb",
    speed_kmh=104.6,
    mpg_us=7.8,
    l_per_100km=30.2,
    notes="Manufacturer-quoted; ideal conditions; no aux loads; aero fairings",
)

ALL_BENCHMARKS = [
    NREL_55MPH,
    NREL_60MPH,
    NREL_65MPH,
    NREL_ALL_DRIVING,
    CASCADIA_SPEC,
]

# ---------------------------------------------------------------------------
# Phase 1 validation acceptance criteria
# ---------------------------------------------------------------------------
# Our model omits auxiliary power loads (~5–10 kW), real-world wind,
# and road roughness.  These typically add 10–20% to fuel consumption.
# We therefore expect our model to be 10–20% optimistic vs NREL cruise data.
# A model error of ≤ 20% is the Phase 1 pass criterion.

PHASE1_TOLERANCE_PCT = 20.0   # maximum acceptable % error vs NREL cruise data
