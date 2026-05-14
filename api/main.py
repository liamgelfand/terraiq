from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from api.config import settings
from api.middleware.request_id import RequestIdMiddleware
from api.routes import analytics, api_keys, auth, batches, billing, corridors, fleet, health, jobs, metrics_route, pilot, telemetry, vehicles
from api.routes.v1 import optimize as v1_optimize
from api.routes.v1 import sweep as v1_sweep

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def _run_migrations() -> None:
    """Apply any pending Alembic migrations at startup."""
    cfg = AlembicConfig("alembic.ini")
    alembic_command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    _run_migrations()
    yield


tags_meta = [
    {"name": "auth", "description": "User registration, login, profile, password reset."},
    {"name": "jobs", "description": "Fleet-scoped optimization jobs (requires JWT)."},
    {"name": "api-keys", "description": "Manage API keys for `/v1/*` public routes."},
    {"name": "analytics", "description": "Aggregate savings for the authenticated fleet."},
    {"name": "vehicles", "description": "Available vehicle profiles for simulations."},
    {"name": "v1", "description": "Public fleet API (`X-API-Key`). Idempotency-Key and webhooks on optimize."},
    {"name": "health", "description": "Liveness and metrics."},
    {"name": "fleet", "description": "Invites, audit log, webhook delivery history, usage, data export / purge."},
    {"name": "corridors", "description": "Saved corridors (lane library) for pilot batch runs."},
    {"name": "batches", "description": "Run optimizations for many corridors at once."},
    {"name": "telemetry", "description": "Upload GPS/speed CSV and compute adherence vs optimized profile."},
    {"name": "pilot", "description": "Ops board, driver brief, pilot CSV bundles."},
    {"name": "billing", "description": "Stripe checkout + webhooks (optional)."},
]


app = FastAPI(
    title="TerraIQ Fleet Intelligence API",
    version="0.2.0",
    description=(
        "Terrain-aware fuel optimization: submit routes (dashboard JWT or public API key), "
        "poll for results or receive webhooks. See tags for internal vs public `/v1` routes."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=tags_meta,
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        openapi_tags=tags_meta,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(metrics_route.router)
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(vehicles.router)
app.include_router(api_keys.router)
app.include_router(analytics.router)
app.include_router(fleet.router)
app.include_router(corridors.router)
app.include_router(batches.router)
app.include_router(telemetry.router)
app.include_router(pilot.router)
app.include_router(billing.router)
app.include_router(v1_optimize.router)
app.include_router(v1_sweep.router)
