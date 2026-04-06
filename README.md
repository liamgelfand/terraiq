# TerraIQ — Terrain-Aware Fuel Optimization

A physics-based fuel optimization engine that computes the ideal speed profile for any route — minimizing total fuel consumption using real-time terrain, traffic, and vehicle data.

## Setup

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

## Project Structure

```
terraiq/
├── data/
│   ├── route_fetcher.py          # Pulls route + elevation from APIs
│   ├── traffic_fetcher.py        # Pulls live/historical traffic data
│   └── vehicle_profiles/
│       ├── base_profile.py       # Abstract base class
│       ├── freightliner_2022.py  # Class 8 truck profile
│       └── toyota_camry_2023.py  # Passenger car profile
├── models/
│   ├── world_model.py            # Route as structured data object
│   ├── vehicle_model.py          # Physics engine — fuel from speed profile
│   └── fuel_map.py               # BSFC map loader and interpolation
├── optimizer/
│   ├── baseline.py               # Constant speed / human driving simulation
│   ├── mpc_optimizer.py          # Core MPC optimization algorithm
│   └── constraints.py            # Speed limits, comfort, traffic constraints
├── simulation/
│   ├── runner.py                 # End-to-end simulation runner
│   └── evaluator.py              # Comparison metrics, output report
├── visualization/
│   └── plotter.py                # Charts: elevation, speed profiles, fuel
├── notebooks/
│   └── experiments.ipynb         # Experimentation and iteration
└── tests/
    └── test_vehicle_model.py     # Validate physics against NREL Fleet DNA data
```

## Build Stages

1. **Route Data Pipeline** — pull real routes with elevation and grade profiles
2. **Vehicle Physics Model** — longitudinal dynamics + BSFC fuel consumption
3. **Baseline Simulator** — benchmark constant-speed human driving
4. **MPC Optimizer** — compute fuel-optimal speed trajectory
5. **Traffic Integration + Multi-Route Testing** — validate at scale

## Phase 1 Success Criterion

Demonstrate ≥8% fuel reduction on 10 diverse real-world highway routes using a validated Class 8 truck physics model, with results replicable within ±2% across runs.
