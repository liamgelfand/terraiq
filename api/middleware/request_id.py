from __future__ import annotations

import logging
import uuid
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("api.request")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Adds X-Request-ID per request and logs a single access line with duration."""

    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = rid
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed method=%s path=%s request_id=%s",
                request.method,
                request.url.path,
                rid,
            )
            raise
        duration_ms = (time.perf_counter() - start) * 1000.0
        response.headers["X-Request-ID"] = rid
        logger.info(
            "method=%s path=%s status=%s duration_ms=%.1f request_id=%s",
            request.method,
            request.url.path,
            getattr(response, "status_code", "?"),
            duration_ms,
            rid,
        )
        return response
