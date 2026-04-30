from __future__ import annotations

import sys

from celery import Celery

from api.config import settings

celery_app = Celery(
    "terraiq",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["api.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Simulations are compute-heavy — process one at a time per worker
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    # Windows does not support the default prefork pool (semaphore restriction)
    worker_pool="solo" if sys.platform == "win32" else "prefork",
)
