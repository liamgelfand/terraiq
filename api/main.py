from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.database import create_tables
from api.routes import api_keys, health, jobs, vehicles
from api.routes.v1 import optimize as v1_optimize


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await create_tables()
    yield


app = FastAPI(
    title="TerraIQ API",
    version="0.1.0",
    description="Terrain-Aware Fuel Optimization — REST API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(vehicles.router)
app.include_router(api_keys.router)
app.include_router(v1_optimize.router)
