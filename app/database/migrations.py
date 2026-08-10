"""
Lightweight schema migrations.

The project's tech stack does not include a migration framework (no
Alembic). `Base.metadata.create_all()` only creates *missing* tables --
it never alters a table that already exists, so when a model gains new
columns after the application has already shipped, those columns must
be added by hand.

`run_migrations()` is the single place that happens. Each migration
function is:

    - Idempotent: safe to run on every startup, every version.
    - Additive only: it adds columns and backfills data; it never
      drops a column or a table, so no data is ever lost even if a
      user's database predates this migration.

This is intentionally simple (raw `ALTER TABLE ... ADD COLUMN`, driven
by `PRAGMA table_info`) rather than a full migration framework, which
would be disproportionate for a single-developer SQLite application at
this stage. If the project grows multiple deployment targets or needs
rollbacks, introducing Alembic later is a drop-in replacement for this
module without touching any other layer.
"""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def run_migrations(engine: Engine) -> None:
    """Run every additive migration, in order. Safe to call on every startup."""
    _migrate_contacts_table(engine)
    _migrate_campaigns_table(engine)
    _migrate_history_table(engine)
    _migrate_campaigns_exhibition_id(engine)
    logger.info("Schema migrations complete.")


def _existing_columns(engine: Engine, table_name: str) -> set[str]:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        # Table doesn't exist yet -- create_all() will create it fresh
        # with every current column, so there is nothing to migrate.
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _migrate_contacts_table(engine: Engine) -> None:
    """
    Sprint 2 replaced `first_name`/`last_name`/`job_title`/`tags`/
    `is_active` on `contacts` with `contact_name`/`website`/
    `stand_number`/`notes`. This adds the new columns if missing and
    backfills `contact_name` from the old `first_name`/`last_name`
    columns when they exist, so nobody who ran Sprint 1 loses data.
    """
    columns = _existing_columns(engine, "contacts")
    if not columns:
        return

    new_columns = {
        "website": "VARCHAR(500)",
        "stand_number": "VARCHAR(120)",
        "notes": "TEXT",
        "contact_name": "VARCHAR(255)",
    }

    with engine.begin() as connection:
        for column_name, column_type in new_columns.items():
            if column_name not in columns:
                connection.execute(
                    text(f"ALTER TABLE contacts ADD COLUMN {column_name} {column_type}")
                )
                logger.info("Migration: added contacts.%s", column_name)

        # Backfill contact_name from the legacy first_name/last_name
        # columns, but only for rows that don't already have it set
        # (so re-running this migration is a no-op).
        if "first_name" in columns:
            connection.execute(
                text(
                    """
                    UPDATE contacts
                    SET contact_name = TRIM(
                        first_name || CASE WHEN last_name IS NOT NULL AND last_name != ''
                                            THEN ' ' || last_name
                                            ELSE '' END
                    )
                    WHERE (contact_name IS NULL OR contact_name = '')
                      AND first_name IS NOT NULL
                    """
                )
            )
            logger.info("Migration: backfilled contacts.contact_name from legacy name columns.")


def _migrate_campaigns_table(engine: Engine) -> None:
    """
    Sprint 2 added `event_name`, `language`, `subject`, and `html_body`
    to `campaigns` so a campaign can carry its own content independent
    of the Template it may have started from. All four are added with a
    SQL-level DEFAULT so existing rows remain valid immediately, matching
    the same defaults declared on the `Campaign` model.
    """
    columns = _existing_columns(engine, "campaigns")
    if not columns:
        return

    new_columns = {
        "event_name": "VARCHAR(255)",
        "language": "VARCHAR(50) NOT NULL DEFAULT 'English'",
        "subject": "VARCHAR(500) NOT NULL DEFAULT ''",
        "html_body": "TEXT NOT NULL DEFAULT ''",
    }

    with engine.begin() as connection:
        for column_name, column_definition in new_columns.items():
            if column_name not in columns:
                connection.execute(
                    text(f"ALTER TABLE campaigns ADD COLUMN {column_name} {column_definition}")
                )
                logger.info("Migration: added campaigns.%s", column_name)


def _migrate_history_table(engine: Engine) -> None:
    """
    Sprint 3 added `sender_account` to `history` so every Outlook test
    send logs which account it was sent from, alongside the existing
    time/recipient/status/error columns.
    """
    columns = _existing_columns(engine, "history")
    if not columns:
        return

    if "sender_account" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE history ADD COLUMN sender_account VARCHAR(255)"))
            logger.info("Migration: added history.sender_account")


def _migrate_campaigns_exhibition_id(engine: Engine) -> None:
    """
    Production Bulk Email Engine: campaigns are now scoped to a real
    Exhibition via `exhibition_id`, instead of the free-text
    `event_name` column. Added nullable so every existing campaign
    keeps loading unchanged and simply falls back to the legacy
    "All Contacts" recipient flow until it is explicitly assigned to
    an Exhibition.
    """
    columns = _existing_columns(engine, "campaigns")
    if not columns:
        return

    if "exhibition_id" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE campaigns ADD COLUMN exhibition_id INTEGER"))
            logger.info("Migration: added campaigns.exhibition_id")
