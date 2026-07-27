"""Blacklist model.

Represents an email address that must never receive a campaign email
(e.g. unsubscribed, bounced, or manually excluded). Enforcement of the
blacklist during sending arrives in a later sprint; this sprint only
defines the storage schema.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Blacklist(Base):
    __tablename__ = "blacklist"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"<Blacklist id={self.id} email={self.email!r}>"
