from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.config import settings
from api.workers.celery_app import celery_app

_sync_engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
_SyncSession = sessionmaker(_sync_engine)


def _arr_to_list(arr) -> list:
    """Safely convert a numpy array or any iterable to a plain Python list."""
    try:
        return arr.tolist()
    except AttributeError:
        return list(arr)


def _result_to_dict(result) -> dict:
    return {
        "route_name": result.route_name,
        "total_distance_km": result.total_distance_km,
        "elevation_gain_m": result.elevation_gain_m,
        "elevation_loss_m": result.elevation_loss_m,
        "total_fuel_liters": result.total_fuel_liters,
        "total_fuel_kg": result.total_fuel_kg,
        "fuel_per_100km": result.fuel_per_100km,
        "vehicle_name": result.vehicle_name,
        "speed_profile_ms": _arr_to_list(result.speed_profile_ms),
        "distances_m": _arr_to_list(result.distances_m),
        "elevations_m": _arr_to_list(result.elevations_m),
        "grades": _arr_to_list(result.grades),
        "speed_limits_ms": _arr_to_list(result.speed_limits_ms),
        "segment_fuel_L": _arr_to_list(result.segment_fuel_L),
        "segment_power_kw": _arr_to_list(result.segment_power_kw),
        "lat": _arr_to_list(result.lat),
        "lon": _arr_to_list(result.lon),
    }


@celery_app.task(bind=True, name="run_simulation")
def run_simulation(self, job_id: str) -> None:  # noqa: ARG001
    from api.models.job import Job  # noqa: PLC0415

    # Mark job as running
    with _SyncSession() as session:
        job = session.get(Job, job_id)
        if not job:
            return
        config = dict(job.config)
        job.status = "running"
        job.updated_at = datetime.now(timezone.utc)
        session.commit()

    try:
        import osmnx as ox  # noqa: PLC0415

        from data.vehicle_profiles.freightliner_2022 import Freightliner2022  # noqa: PLC0415
        from simulation.evaluator import EvaluationReport  # noqa: PLC0415
        from simulation.runner import SimulationRunner  # noqa: PLC0415

        origin_coords: tuple[float, float] = ox.geocode(config["origin"])
        dest_coords: tuple[float, float] = ox.geocode(config["destination"])
        route_name = f"{config['origin']} to {config['destination']}"

        vehicle = Freightliner2022()

        # Apply payload weight if provided — overrides default fully-laden mass
        load_kg = config.get("load_kg")
        if load_kg is not None:
            vehicle.mass_kg = vehicle.tare_mass_kg + float(load_kg)

        runner = SimulationRunner(vehicle)

        baseline = runner.run(
            origin=origin_coords,
            destination=dest_coords,
            route_name=route_name,
        )

        optimized = runner.run_optimized(
            origin=origin_coords,
            destination=dest_coords,
            route_name=route_name,
        )

        report = EvaluationReport(baseline=baseline, optimized=optimized)

        result = {
            "baseline": _result_to_dict(baseline),
            "optimized": _result_to_dict(optimized),
            "savings": {
                "fuel_saved_liters": report.fuel_saved_liters,
                "fuel_saved_pct": report.fuel_saved_pct,
                "cost_saved_usd": report.cost_saved_usd,
                "co2_saved_kg": report.co2_saved_kg,
            },
        }

        with _SyncSession() as session:
            job = session.get(Job, job_id)
            if job:
                job.status = "completed"
                job.result = result
                job.completed_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                session.commit()

    except Exception as exc:
        with _SyncSession() as session:
            job = session.get(Job, job_id)
            if job:
                job.status = "failed"
                job.error_message = str(exc)
                job.updated_at = datetime.now(timezone.utc)
                session.commit()
        raise
