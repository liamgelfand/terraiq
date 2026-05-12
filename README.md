# TerraIQ

**Terrain-Aware Fuel Optimization** — a physics-based route intelligence API that computes the optimal speed profile for any highway route, minimizing fuel consumption using real terrain grades, vehicle dynamics, and Model Predictive Control.

Designed for commercial fleet operators. Delivers 8–15% fuel savings on mountain and rolling-terrain routes.

---

## Architecture

```
┌─────────────────────┐     ┌──────────────────────────────────────┐
│   React + Vite UI   │────▶│  FastAPI   (REST + JWT auth)         │
│   Tailwind / shadcn │     │  ├── /auth/*       User & fleet mgmt │
└─────────────────────┘     │  ├── /api/*        Internal dashboard│
                            │  └── /v1/optimize  Public API (keys) │
                            └──────────┬───────────────────────────┘
                                       │ Celery task
                            ┌──────────▼───────────────────────────┐
                            │  Simulation + MPC Optimizer           │
                            │  OSMnx road graph · CasADi/IPOPT     │
                            │  BSFC fuel map · longitudinal physics │
                            └──────────────────────────────────────┘
                            ┌────────────┐  ┌────────────────────┐
                            │ PostgreSQL │  │ Redis (broker +    │
                            │ (jobs, DB) │  │  rate limiter)     │
                            └────────────┘  └────────────────────┘
```

## Quick Start

**Prerequisites:** Python 3.11+, Node 18+, Docker Desktop

```bash
# 1. Clone and create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 2. Install all dependencies
make install

# 3. Copy environment config
cp .env.example .env

# 4. Start all services (Docker + API + Celery + Frontend)
make dev
```

Open [http://localhost:5173](http://localhost:5173).

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Project Structure

```
terraiq/
├── api/                    FastAPI application
│   ├── models/             SQLAlchemy ORM models
│   ├── routes/             HTTP route handlers
│   │   └── v1/             Public API (API key auth)
│   ├── schemas/            Pydantic request/response schemas
│   └── workers/            Celery tasks
│
├── simulation/             End-to-end simulation pipeline
│   ├── runner.py           Route → fuel result
│   └── evaluator.py        Baseline vs optimized comparison
│
├── optimizer/              MPC optimization core
│   ├── mpc_optimizer.py    CasADi / IPOPT NLP solver
│   ├── baseline.py         Human-driving speed profile
│   └── constraints.py      Speed limits, comfort bounds
│
├── models/                 Physics models
│   ├── vehicle_model.py    Longitudinal dynamics + fuel
│   ├── world_model.py      Route as structured data
│   └── fuel_map.py         BSFC map interpolation
│
├── data/                   Data fetching and vehicle profiles
│   ├── route_fetcher.py    OSMnx road graph + elevation
│   └── vehicle_profiles/   Per-vehicle physics parameters
│
├── validation/             Physics validation against NREL data
├── visualization/          Matplotlib plotting utilities
├── scripts/                Developer CLI tools (local use)
│   ├── run_simulation.py   Single-route physics debug run
│   └── run_batch.py        Multi-route validation suite
│
├── migrations/             Alembic DB migrations
├── tests/                  Test suite
│   ├── unit/               Pure function tests (no I/O)
│   └── integration/        HTTP + SQLite + fakeredis
├── e2e/                    Playwright end-to-end tests
└── frontend/               React + Vite application
    └── src/
        ├── pages/          Dashboard, History, Analytics, etc.
        ├── components/     Shared UI components
        ├── api/            API client + TypeScript types
        ├── contexts/       React context (auth state)
        └── hooks/          React Query hooks
```

---

## Common Commands

```bash
make dev               # Start all services
make stop              # Stop Docker

make test              # All tests (backend + frontend)
make test-unit         # Fast unit tests only (~7s)
make test-integration  # Integration tests (~20s)
make test-fe           # Frontend component tests

make migrate           # Apply DB migrations
make migration msg=X   # Generate new migration

make help              # Full command reference
```

## Testing

```bash
# Backend (99 tests)
make test-be

# Frontend (25 tests)
make test-fe

# E2E — requires make dev running first
make test-e2e
```

---

## API Usage

The public API uses API key authentication via the `X-API-Key` header.

```bash
# Submit an optimization job
curl -X POST http://localhost:8000/v1/optimize \
  -H "X-API-Key: tiq_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"origin": "Denver, CO", "destination": "Grand Junction, CO"}'

# Poll for result
curl http://localhost:8000/v1/optimize/{job_id} \
  -H "X-API-Key: tiq_your_key_here"
```

Full interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)
