"""Dispatch signed webhooks when async jobs complete (called from Celery workers)."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from typing import Any

import httpx

from api.config import settings
from api.models.job import Job
from api.models.webhook_delivery import WebhookDelivery
from api.sync_db import SyncSession

logger = logging.getLogger(__name__)


def _sign_body(body_bytes: bytes) -> tuple[dict[str, str], str]:
    sig = hmac.new(
        settings.webhook_signing_secret.encode("utf-8"),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-TerraIQ-Signature": f"sha256={sig}",
        "User-Agent": "TerraIQ-Webhook/1.1",
    }
    return headers, sig


def deliver_job_webhook_once(job_id: str, attempt: int) -> tuple[bool, str | None]:
    """
    Single delivery attempt. Returns (success, error_message).
    Success True when no URL is configured or HTTP 2xx is received.
    """
    with SyncSession() as session:
        job = session.get(Job, job_id)
        if not job or job.status not in ("completed", "failed"):
            return True, None
        cfg = dict(job.config)
        url = (cfg or {}).get("webhook_url")
        if not url or not str(url).strip():
            return True, None
        status = job.status
        result = job.result if status == "completed" else None
        err_msg = job.error_message
        err_code = job.error_code
        event = "job.completed" if status == "completed" else "job.failed"
        url_str = str(url).strip()

    body_obj: dict[str, Any] = {
        "event": event,
        "job_id": job_id,
        "status": status,
        "result": result,
        "error": err_msg,
        "error_code": err_code,
    }
    body_bytes = json.dumps(body_obj, separators=(",", ":"), default=str).encode("utf-8")
    hdr, _sig = _sign_body(body_bytes)
    hdr["X-TerraIQ-Event"] = event

    err_out: str | None = None
    http_status: int | None = None
    try:
        with httpx.Client(timeout=25.0, follow_redirects=True) as client:
            r = client.post(url_str, content=body_bytes, headers=hdr)
            http_status = r.status_code
            r.raise_for_status()
        logger.info(
            "Webhook delivered job_id=%s attempt=%s status=%s", job_id, attempt, http_status
        )
    except Exception as exc:  # noqa: BLE001
        err_out = str(exc)
        logger.warning("Webhook attempt failed job_id=%s attempt=%s: %s", job_id, attempt, exc)

    with SyncSession() as session:
        session.add(
            WebhookDelivery(
                id=str(uuid.uuid4()),
                job_id=job_id,
                url=url_str[:8000],
                event=event,
                attempt=attempt,
                http_status=http_status,
                error_message=(err_out or "")[:8000] if err_out else None,
            )
        )
        session.commit()

    if http_status is not None and 200 <= http_status < 300:
        return True, None
    return False, err_out or f"HTTP {http_status}"


def dispatch_job_webhook(*, job_id: str, **kwargs: Any) -> None:
    """Backward-compatible name; extra fields ignored."""
    deliver_job_webhook_once(job_id, attempt=1)
