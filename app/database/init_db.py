"""
Database initialization.

`initialize_database()` is the single entry point the application calls
at startup. It:

    1. Ensures every model is imported (so `Base.metadata` is complete).
    2. Creates any missing tables (never drops or alters existing ones).
    3. Runs additive schema migrations for tables that already existed
       under an older model shape (see `app/database/migrations.py`).
    4. Seeds default rows into the `settings` table on first run only.

This module deliberately contains no business logic beyond bootstrapping
storage -- it is infrastructure, not a service.
"""

from __future__ import annotations

import logging

# Importing app.models ensures every ORM class registers itself against
# Base.metadata before create_all() is called.
import app.models  # noqa: F401
from app.config.constants import DEFAULT_SETTINGS
from app.database.base import Base, get_engine, session_scope
from app.database.migrations import run_migrations
from app.models.lead_stage import LeadStage
from app.models.setting import Setting

logger = logging.getLogger(__name__)

# The single default stage a new ExhibitionContact lands in. Full stage
# management (adding/reordering/deleting stages) is out of scope for
# this milestone -- this is the one seeded row LeadStage needs to exist
# as a persisted model rather than a hard-coded enum.
DEFAULT_LEAD_STAGE_NAME = "New"


def initialize_database() -> None:
    """Create all tables (if missing), migrate existing ones, and seed default rows."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema verified/created.")

    run_migrations(engine)

    _seed_default_settings()
    _seed_default_lead_stage()


def _seed_default_lead_stage() -> None:
    """Insert the single default LeadStage ("New") on first run only."""
    with session_scope() as session:
        existing = session.query(LeadStage).filter(LeadStage.name == DEFAULT_LEAD_STAGE_NAME).first()
        if existing is not None:
            return
        session.add(LeadStage(name=DEFAULT_LEAD_STAGE_NAME, sort_order=0, is_default=True))
        logger.info("Seeded default lead stage: %s", DEFAULT_LEAD_STAGE_NAME)


def _seed_default_settings() -> None:
    """Insert each default setting only if it does not already exist."""
    with session_scope() as session:
        existing_keys = {row.key for row in session.query(Setting.key).all()}

        created_count = 0
        for setting_key, (default_value, value_type) in DEFAULT_SETTINGS.items():
            if setting_key.value in existing_keys:
                continue
            session.add(
                Setting(
                    key=setting_key.value,
                    value=default_value,
                    value_type=value_type.value,
                )
            )
            created_count += 1

        if created_count:
            logger.info("Seeded %d default setting(s).", created_count)
