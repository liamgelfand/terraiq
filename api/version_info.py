"""Released app version and simulation engine lineage (bump when physics/solver materially changes)."""

from __future__ import annotations

# Keep in sync with FastAPI `app.version` in `api/main.py` for human-facing docs.
APP_VERSION = "0.2.0"

# Bump when optimizer / vehicle model / evaluation semantics change materially.
SIMULATION_ENGINE_VERSION = "1.0.0"
