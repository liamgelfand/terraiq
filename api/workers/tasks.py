from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery.exceptions import MaxRetriesExceededError

from api.sync_db import SyncSession
from api.vehicle_factory import get_vehicle_instance
from api.version_info import APP_VERSION, SIMULATION_ENGINE_VERSION
from api.webhooks import deliver_job_webhook_once
from api.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Exceptions worth retrying automatically (network / transient faults)
_RETRIABLE = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def _arr_to_list(arr) -> list:
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


def _classify_simulation_error(exc: BaseException) -> str:
    msg = str(exc).lower()
    if "geocode" in msg or "could not geocode" in msg:
        return "GEOCODE_FAILED"
    if "ipopt" in msg or "solver" in msg or "infeasible" in msg:
        return "SOLVER_FAILED"
    if "route" in msg and "fetch" in msg:
        return "ROUTE_FETCH_FAILED"
    return "SIMULATION_FAILED"


@celery_app.task(
    bind=True,
    name="deliver_webhook",
    max_retries=5,
    default_retry_delay=15,
)
def deliver_webhook(self, job_id: str) -> None:
    """Queued webhook delivery with Celery retries (see also webhook_deliveries table)."""
    ok, err = deliver_job_webhook_once(job_id, attempt=self.request.retries + 1)
    if ok:
        return
    countdown = min(300, 15 * (2**self.request.retries))
    try:
        raise self.retry(exc=RuntimeError(err or "webhook failed"), countdown=countdown)
    except MaxRetriesExceededError:
        logger.error("Webhook delivery exhausted job_id=%s", job_id)


def _notify_webhook(job_id: str) -> None:
    deliver_webhook.delay(job_id)


def _apply_lineage(config: dict, result: dict) -> dict:
    lineage = {
        "app_version": APP_VERSION,
        "vehicle_profile_id": config.get("vehicle_id"),
        "job_type": config.get("job_type", "optimize"),
    }
    r = dict(result)
    r["lineage"] = {**lineage, "simulation_engine_version": SIMULATION_ENGINE_VERSION}
    return r


def _maybe_finalize_batch(batch_id: str | None) -> None:
    if not batch_id:
        return
    from sqlalchemy import func, select

    from api.models.job import Job
    from api.models.job_batch import JobBatch

    with SyncSession() as session:
        batch = session.get(JobBatch, batch_id)
        if not batch or batch.status not in ("pending", "running"):
            return
        pending = session.scalar(
            select(func.count()).select_from(Job).where(
                Job.batch_id == batch_id,
                Job.status.in_(["pending", "running"]),
            )
        )
        if pending and pending > 0:
            return
        total = session.scalar(
            select(func.count()).select_from(Job).where(Job.batch_id == batch_id)
        ) or 0
        completed = session.scalar(
            select(func.count()).select_from(Job).where(
                Job.batch_id == batch_id, Job.status == "completed"
            )
        ) or 0
        failed = session.scalar(
            select(func.count()).select_from(Job).where(
                Job.batch_id == batch_id, Job.status == "failed"
            )
        ) or 0
        batch.status = "failed" if completed == 0 and failed == total else "completed"
        batch.completed_at = datetime.now(timezone.utc)
        batch.updated_at = datetime.now(timezone.utc)
        batch.summary = {
            "total": int(total),
            "completed": int(completed),
            "failed": int(failed),
        }
        session.commit()

    _email_batch_complete(batch_id)


def _email_batch_complete(batch_id: str) -> None:
    from sqlalchemy import select

    from api.emailer import send_email_sync
    from api.models.job_batch import JobBatch
    from api.models.user import User

    with SyncSession() as session:
        batch = session.get(JobBatch, batch_id)
        if not batch:
            return
        summ = dict(batch.summary or {})
        display_name = batch.name
        fleet_id = batch.fleet_id
        admins = session.execute(
            select(User).where(User.fleet_id == fleet_id, User.role == "admin")
        )
        emails = [u.email for u in admins.scalars().all()]

    body = (
        f"<p>Your batch <b>{display_name or batch_id[:8]}</b> finished.</p>"
        f"<p>Total jobs: {summ.get('total', 0)}, completed: {summ.get('completed', 0)}, "
        f"failed: {summ.get('failed', 0)}.</p>"
    )
    for to in emails:
        send_email_sync("TerraIQ: batch run complete", body, to)


def _email_telemetry_complete(upload_id: str) -> None:
    from sqlalchemy import select

    from api.emailer import send_email_sync
    from api.models.telemetry_upload import TelemetryUpload
    from api.models.user import User

    with SyncSession() as session:
        up = session.get(TelemetryUpload, upload_id)
        if not up:
            return
        pct = (up.adherence or {}).get("pct_in_band")
        fleet_id = up.fleet_id
        admins = session.execute(
            select(User).where(User.fleet_id == fleet_id, User.role == "admin")
        )
        emails = [u.email for u in admins.scalars().all()]

    body = f"<p>Telemetry upload <code>{upload_id[:8]}</code> was processed.</p>"
    if pct is not None:
        body += f"<p>Adherence (in recommended band): <b>{pct}%</b>.</p>"
    for to in emails:
        send_email_sync("TerraIQ: telemetry processed", body, to)


def _set_job_failed(
    job_id: str, message: str, code: str, *, notify: bool = True
) -> None:
    from api.models.job import Job  # noqa: PLC0415

    batch_id = None
    with SyncSession() as session:
        job = session.get(Job, job_id)
        if job:
            batch_id = job.batch_id
            job.status = "failed"
            job.error_message = message
            job.error_code = code
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
    if notify:
        _notify_webhook(job_id)
    _maybe_finalize_batch(batch_id)


# Time budgets for the Pareto sweep (fraction of baseline travel time)
_SWEEP_BUDGETS = [1.0, 1.03, 1.05, 1.10, 1.15, 1.25]


@celery_app.task(
    bind=True,
    name="run_simulation",
    max_retries=3,
    default_retry_delay=30,
)
def run_simulation(self, job_id: str) -> None:
    from api.models.job import Job  # noqa: PLC0415

    with SyncSession() as session:
        job = session.get(Job, job_id)
        if not job:
            return
        config = dict(job.config)
        job.status = "running"
        job.updated_at = datetime.now(timezone.utc)
        session.commit()

    try:
        import osmnx as ox  # noqa: PLC0415

        from simulation.evaluator import EvaluationReport  # noqa: PLC0415
        from simulation.runner import SimulationRunner  # noqa: PLC0415

        origin_coords: tuple[float, float] = ox.geocode(config["origin"])
        dest_coords: tuple[float, float] = ox.geocode(config["destination"])
        route_name = f"{config['origin']} to {config['destination']}"

        vehicle = get_vehicle_instance(config.get("vehicle_id"))
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
        result = _apply_lineage(config, result)
        lineage_store = {
            "app_version": APP_VERSION,
            "vehicle_profile_id": config.get("vehicle_id"),
            "job_type": config.get("job_type", "optimize"),
        }

        batch_id = None
        with SyncSession() as session:
            job = session.get(Job, job_id)
            if job:
                batch_id = job.batch_id
                job.status = "completed"
                job.result = result
                job.lineage = lineage_store
                job.simulation_engine_version = SIMULATION_ENGINE_VERSION
                job.error_code = None
                job.completed_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                session.commit()

        _notify_webhook(job_id)
        _maybe_finalize_batch(batch_id)

    except _RETRIABLE as exc:
        attempt = self.request.retries
        countdown = 30 * (2 ** attempt)
        logger.warning(
            "run_simulation job=%s retriable error (attempt %d): %s — retrying in %ds",
            job_id,
            attempt + 1,
            exc,
            countdown,
        )
        try:
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            _set_job_failed(
                job_id,
                f"Failed after {self.max_retries} retries: {exc}",
                "TRANSPORT_EXHAUSTED",
            )

    except Exception as exc:
        code = _classify_simulation_error(exc)
        logger.exception("run_simulation job=%s permanent failure: %s", job_id, exc)
        _set_job_failed(job_id, str(exc), code)


@celery_app.task(
    bind=True,
    name="run_sweep",
    max_retries=2,
    default_retry_delay=60,
)
def run_sweep(self, job_id: str) -> None:
    from api.models.job import Job  # noqa: PLC0415

    with SyncSession() as session:
        job = session.get(Job, job_id)
        if not job:
            return
        config = dict(job.config)
        job.status = "running"
        job.updated_at = datetime.now(timezone.utc)
        session.commit()

    try:
        import osmnx as ox  # noqa: PLC0415

        from simulation.evaluator import EvaluationReport  # noqa: PLC0415
        from simulation.runner import SimulationRunner  # noqa: PLC0415

        origin_coords: tuple[float, float] = ox.geocode(config["origin"])
        dest_coords: tuple[float, float] = ox.geocode(config["destination"])
        route_name = f"{config['origin']} to {config['destination']}"

        vehicle = get_vehicle_instance(config.get("vehicle_id"))
        load_kg = config.get("load_kg")
        if load_kg is not None:
            vehicle.mass_kg = vehicle.tare_mass_kg + float(load_kg)

        runner = SimulationRunner(vehicle)

        baseline = runner.run(
            origin=origin_coords,
            destination=dest_coords,
            route_name=route_name,
        )

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

                avg_base = (
                    sum(baseline.speed_profile_ms) / len(baseline.speed_profile_ms)
                    if baseline.speed_profile_ms
                    else 1.0
                )
                avg_opt = (
                    sum(opt.speed_profile_ms) / len(opt.speed_profile_ms)
                    if opt.speed_profile_ms
                    else avg_base
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
                continue

        result = {
            "distance_km": round(baseline.total_distance_km, 2),
            "baseline_fuel_L": round(baseline.total_fuel_liters, 3),
            "curve": curve,
        }
        result = _apply_lineage(config, result)
        lineage_store = {
            "app_version": APP_VERSION,
            "vehicle_profile_id": config.get("vehicle_id"),
            "job_type": config.get("job_type", "sweep"),
        }

        batch_id = None
        with SyncSession() as session:
            job = session.get(Job, job_id)
            if job:
                batch_id = job.batch_id
                job.status = "completed"
                job.result = result
                job.lineage = lineage_store
                job.simulation_engine_version = SIMULATION_ENGINE_VERSION
                job.error_code = None
                job.completed_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                session.commit()

        _notify_webhook(job_id)
        _maybe_finalize_batch(batch_id)

    except _RETRIABLE as exc:
        attempt = self.request.retries
        countdown = 60 * (2 ** attempt)
        logger.warning(
            "run_sweep job=%s retriable error (attempt %d): %s — retrying in %ds",
            job_id,
            attempt + 1,
            exc,
            countdown,
        )
        try:
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            _set_job_failed(
                job_id,
                f"Failed after {self.max_retries} retries: {exc}",
                "TRANSPORT_EXHAUSTED",
            )

    except Exception as exc:
        code = _classify_simulation_error(exc)
        logger.exception("run_sweep job=%s permanent failure: %s", job_id, exc)
        _set_job_failed(job_id, str(exc), code)


@celery_app.task(name="run_batch")
def run_batch(batch_id: str) -> None:
    import uuid

    from api.models.job import Job
    from api.models.job_batch import JobBatch
    from api.models.saved_corridor import SavedCorridor

    with SyncSession() as session:
        batch = session.get(JobBatch, batch_id)
        if not batch:
            return
        cfg = dict(batch.config or {})
        cids = list(cfg.get("corridor_ids") or [])
        if not cids:
            batch.status = "failed"
            batch.error_message = "no_corridors"
            batch.updated_at = datetime.now(timezone.utc)
            session.commit()
            return
        batch.status = "running"
        batch.updated_at = datetime.now(timezone.utc)
        session.commit()

    created = 0
    for cid in cids:
        jid = None
        with SyncSession() as session:
            batch = session.get(JobBatch, batch_id)
            cor = session.get(SavedCorridor, cid)
            if not batch or not cor or cor.fleet_id != batch.fleet_id:
                continue
            job = Job(
                id=str(uuid.uuid4()),
                fleet_id=batch.fleet_id,
                batch_id=batch.id,
                corridor_id=cor.id,
                status="pending",
                config={
                    "origin": cor.origin,
                    "destination": cor.destination,
                    "vehicle_id": cor.vehicle_id,
                    "job_type": "optimize",
                    "load_kg": cor.load_kg,
                    "time_budget_fraction": cor.time_budget_fraction,
                },
            )
            session.add(job)
            session.commit()
            jid = job.id
            created += 1
        if jid:
            run_simulation.delay(jid)

    if created == 0:
        with SyncSession() as session:
            batch = session.get(JobBatch, batch_id)
            if batch:
                batch.status = "failed"
                batch.error_message = "no_valid_corridors"
                batch.updated_at = datetime.now(timezone.utc)
                session.commit()


@celery_app.task(
    bind=True,
    name="process_telemetry_upload",
    max_retries=30,
    default_retry_delay=20,
)
def process_telemetry_upload(self, upload_id: str) -> None:
    from api.models.job import Job
    from api.models.telemetry_upload import TelemetryUpload
    from api.services.telemetry_adherence import compute_adherence

    points: list | None = None
    job_id: str | None = None
    with SyncSession() as session:
        up = session.get(TelemetryUpload, upload_id)
        if not up:
            return
        points = up.points
        job_id = up.job_id

    if not points:
        with SyncSession() as session:
            up = session.get(TelemetryUpload, upload_id)
            if up:
                up.status = "failed"
                up.error_message = "no_points"
                up.updated_at = datetime.now(timezone.utc)
                session.commit()
        return

    if not job_id:
        with SyncSession() as session:
            up = session.get(TelemetryUpload, upload_id)
            if up:
                up.status = "failed"
                up.error_message = "job_id_required"
                up.updated_at = datetime.now(timezone.utc)
                session.commit()
        return

    with SyncSession() as session:
        job = session.get(Job, job_id)

    if not job:
        with SyncSession() as session:
            up = session.get(TelemetryUpload, upload_id)
            if up:
                up.status = "failed"
                up.error_message = "job_not_found"
                up.updated_at = datetime.now(timezone.utc)
                session.commit()
        return

    if job.status == "failed":
        with SyncSession() as session:
            up = session.get(TelemetryUpload, upload_id)
            if up:
                up.status = "failed"
                up.error_message = "job_failed"
                up.updated_at = datetime.now(timezone.utc)
                session.commit()
        return

    if job.status != "completed" or not job.result:
        logger.info("telemetry upload %s waiting on job %s", upload_id, job_id)
        try:
            raise self.retry(exc=RuntimeError("job_not_ready"))
        except MaxRetriesExceededError:
            with SyncSession() as session:
                up = session.get(TelemetryUpload, upload_id)
                if up:
                    up.status = "failed"
                    up.error_message = "job_never_completed"
                    up.updated_at = datetime.now(timezone.utc)
                    session.commit()
        return

    adherence = compute_adherence(dict(job.result), list(points), tolerance_kmh=12.0)
    with SyncSession() as session:
        up = session.get(TelemetryUpload, upload_id)
        if up:
            up.status = "processed"
            up.adherence = adherence
            up.updated_at = datetime.now(timezone.utc)
            session.commit()

    _email_telemetry_complete(upload_id)
