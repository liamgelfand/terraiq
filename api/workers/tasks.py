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


# Time budgets for the Pareto sweep (fraction of baseline travel time)
_SWEEP_BUDGETS = [1.0, 1.03, 1.05, 1.10, 1.15, 1.25]


@celery_app.task(bind=True, name="run_sweep")
def run_sweep(self, job_id: str) -> None:  # noqa: ARG001
    """
    Runs the MPC optimizer at several time budgets for the same route,
    producing a cost-vs-time Pareto curve.
    """
    from api.models.job import Job  # noqa: PLC0415

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
        load_kg = config.get("load_kg")
        if load_kg is not None:
            vehicle.mass_kg = vehicle.tare_mass_kg + float(load_kg)

        runner = SimulationRunner(vehicle)

        # Run baseline once — route is cached after this call
        baseline = runner.run(
            origin=origin_coords,
            destination=dest_coords,
            route_name=route_name,
        )
        baseline_time_s = float(baseline.distances_m[-1]) / float(
            baseline.speed_profile_ms[:-1].mean() if hasattr(baseline.speed_profile_ms, "mean")
            else sum(baseline.speed_profile_ms[:-1]) / max(len(baseline.speed_profile_ms) - 1, 1)
        ) if len(baseline.speed_profile_ms) > 1 else 0.0

        curve = []
        for tbf in _SWEEP_BUDGETS:
            try:
                opt = runner.run_optimized(
                    origin=origin_coords,
                    destination=dest_coords,
                    route_name=route_name,
                    time_budget_fraction=tbf,
                )
                report = EvaluationReport(baseline=baseline, optimized=opt)

                # Estimate extra time vs baseline travel time
                # Using average speed ratio as a proxy for travel time ratio
                avg_base = (
                    sum(baseline.speed_profile_ms) / len(baseline.speed_profile_ms)
                    if baseline.speed_profile_ms else 1.0
                )
                avg_opt = (
                    sum(opt.speed_profile_ms) / len(opt.speed_profile_ms)
                    if opt.speed_profile_ms else avg_base
                )
                dist_m = (
                    baseline.distances_m[-1]
                    if hasattr(baseline.distances_m, "__len__") and len(baseline.distances_m)
                    else 100_000.0
                )
                base_time_s = dist_m / avg_base if avg_base > 0 else 1.0
                opt_time_s = dist_m / avg_opt if avg_opt > 0 else base_time_s
                extra_time_min = max(0.0, (opt_time_s - base_time_s) / 60.0)

                curve.append({
                    "time_budget_fraction": tbf,
                    "extra_time_min": round(extra_time_min, 1),
                    "fuel_saved_L": round(report.fuel_saved_liters, 3),
                    "fuel_saved_pct": round(report.fuel_saved_pct, 2),
                    "cost_saved_usd": round(report.cost_saved_usd, 2),
                    "co2_saved_kg": round(report.co2_saved_kg, 2),
                })
            except Exception:  # noqa: BLE001
                # If one budget fails, skip it and continue
                continue

        result = {
            "distance_km": round(baseline.total_distance_km, 2),
            "baseline_fuel_L": round(baseline.total_fuel_liters, 3),
            "curve": curve,
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
