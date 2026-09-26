# TerraIQ

**Terrain-aware fuel optimization** — a physics-based route intelligence API that computes a recommended speed profile for highway routes using real terrain grades, vehicle dynamics, and Model Predictive Control.

Built for commercial fleet operators on repeating mountain and rolling-terrain lanes. Simulated savings are a planning number; treat measured fuel and speed adherence as the commercial result. Do not advertise a guaranteed percentage until a corridor has been measured on the truck.

---

## Architecture

```
┌─────────────────────┐     ┌──────────────────────────────────────┐
│   React + Vite UI   │────▶│  FastAPI   (REST + JWT auth)         │
│   Tailwind / shadcn │     │  ├── /auth/*       User & fleet mgmt │
│   Landing + legal   │     │  ├── /api/*        Internal dashboard│
└─────────────────────┘     │  ├── /v1/optimize  Public API (keys) │
                            │  └── /api/public   Demo / pilot leads│
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

Trial fleets can run a limited number of jobs and corridors per month. A paid **pilot** plan (Stripe, when configured) raises those limits.

---

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

Open [http://localhost:5173](http://localhost:5173) — marketing landing, then Sign in / Create account.

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Production-style stack (paid pilot host)

Set `DEBUG=false`, a real `JWT_SECRET`, and a real `WEBHOOK_SIGNING_SECRET` in `.env`. Optionally configure Stripe, Resend, and `DEMO_REQUEST_EMAIL`.

```bash
make prod
```

The SPA is served on [http://localhost](http://localhost) and nginx proxies `/api`, `/v1`, `/auth`, `/docs`, `/health`, and `/ready` to the API. Postgres and Redis ports are not published.

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
├── docker-compose.prod.yml Production compose (nginx :80)
└── frontend/               React + Vite application
    └── src/
        ├── pages/          Landing, Dashboard, Ops, legal, briefs
        ├── components/     Shared UI components
        ├── api/            API client + TypeScript types
        ├── contexts/       React context (auth state)
        └── hooks/          React Query hooks
```

---

## Common Commands

```bash
make dev               # Start all services
make prod              # Production compose (requires .env secrets)
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
# Backend
make test-be

# Frontend
make test-fe

# E2E — requires make dev running first
make test-e2e
```

---

## API Usage

The public API uses API key authentication via the `X-API-Key` header. Trial quotas apply per fleet (HTTP 402 when exceeded).

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

---

## Selling a pilot

This product is sold as a **paid 60–90 day pilot**, not open self-serve SaaS:

1. Host with `make prod` (HTTPS in front of nginx in real deployments).
2. Configure Stripe (`STRIPE_PRICE_PILOT_MONTHLY`) and Resend.
3. Use the landing page and `/api/public/demo-request` for inbound leads.
4. Onboard 5–15 repeating corridors, print driver briefs from the ops board, collect GPS/speed CSVs for adherence.
5. Quote measured adherence and fuel — not a generic percentage.
