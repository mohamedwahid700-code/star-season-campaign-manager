"""
Logging service.

`app/utils/logger.py` configures *how* logging works (handlers, file
rotation). This service is the application-facing surface other layers
use to actually emit log records, optionally persisting important
events to the `logs` table so a future "Activity" page can display
them without parsing log files.

Plain Python logging (`logging.getLogger(__name__)`) remains perfectly
valid throughout the codebase for routine debug/info/error messages.
Use `LoggingService.log_event(...)` specifically for events that should
survive in the database as user-facing history (e.g. "Campaign X
started"), not for every line of diagnostic output.
"""

from __future__ import annotations

import logging

from app.models.log import Log
from app.repositories.log_repository import LogRepository


class LoggingService:
    def __init__(self, repository: LogRepository | None = None) -> None:
        self._repository = repository or LogRepository()
        self._logger = logging.getLogger("app.activity")

    def log_event(self, level: str, message: str, source: str | None = None) -> None:
        """Emit a log record through the standard logger and persist it to the database."""
        numeric_level = logging.getLevelName(level.upper())
        if not isinstance(numeric_level, int):
            numeric_level = logging.INFO

        self._logger.log(numeric_level, "[%s] %s", source or "app", message)

        self._repository.add(Log(level=level.upper(), source=source, message=message))

    def get_recent_events(self, limit: int = 100) -> list[Log]:
        return self._repository.get_recent(limit=limit)
