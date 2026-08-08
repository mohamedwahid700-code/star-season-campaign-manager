"""Contact model.

Represents a single exhibition participant / prospective client that
campaigns can be sent to.

Sprint 2 replaces the generic first/last name shape from Sprint 1 with
the exhibition-specific field set requested for Contact Management
(company name, website, stand number, notes, ...). See
`app/database/migrations.py` for how any pre-existing `contacts` table
is upgraded in place without losing data.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stand_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    history_entries: Mapped[list["History"]] = relationship(
        back_populates="contact", cascade="all, delete-orphan"
    )
    exhibition_links: Mapped[list["ExhibitionContact"]] = relationship(
        back_populates="contact", cascade="all, delete-orphan"
    )

    @property
    def display_name(self) -> str:
        """Best-effort human-readable label for tables and dropdowns."""
        if self.contact_name:
            return self.contact_name
        if self.company:
            return self.company
        return self.email

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"<Contact id={self.id} email={self.email!r}>"
