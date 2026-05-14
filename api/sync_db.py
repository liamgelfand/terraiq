"""Shared synchronous SQLAlchemy session for Celery workers and webhook delivery."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.config import settings

_engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
SyncSession = sessionmaker(_engine)
