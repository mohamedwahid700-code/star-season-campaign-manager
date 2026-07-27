"""Log model.

Daily rotating *file* logs (see `app/utils/logger.py`) are the primary
logging mechanism and are always active. This table exists so that a
future "Activity Log" UI page can display important events (campaign
started, contact imported, email failed, ...) without parsing log
files. Sprint 1 defines the schema only; nothing writes to this table
yet.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"<Log id={self.id} level={self.level} source={self.source!r}>"
