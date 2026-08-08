"""Exhibition model.

Represents a single exhibition/event (Big 5, LEAP, Saudi Event Show,
...). This is the central operational entity the Master Project
Document requires: campaigns and participant relationships are scoped
to an Exhibition via `ExhibitionContact`, rather than participants
being tracked only as a flat, unscoped Contact list.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Exhibition(Base):
    __tablename__ = "exhibitions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    participants: Mapped[list["ExhibitionContact"]] = relationship(
        back_populates="exhibition", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"<Exhibition id={self.id} name={self.name!r}>"
