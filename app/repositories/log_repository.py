"""Repository for `Log` records (database-backed activity log).

Not written to in Sprint 1 -- the schema exists so a future "Activity"
UI page can be built against a stable contract. See `app/utils/logger.py`
for the file-based logging system that *is* active this sprint.
"""

from __future__ import annotations

from app.database.base import session_scope
from app.models.log import Log
from app.repositories.base_repository import BaseRepository


class LogRepository(BaseRepository[Log]):
    def __init__(self) -> None:
        super().__init__(Log)

    def get_recent(self, limit: int = 100) -> list[Log]:
        with session_scope() as session:
            return (
                session.query(Log)
                .order_by(Log.created_at.desc())
                .limit(limit)
                .all()
            )
