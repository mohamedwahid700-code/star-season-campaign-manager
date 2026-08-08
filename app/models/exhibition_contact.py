"""ExhibitionContact model.

Per-exhibition membership record. `Contact` remains the single global
identity, deduplicated by email; `ExhibitionContact` is the join entity
that says "this Contact participates in this Exhibition", carrying the
exhibition-specific facts (stand number, where the row came from, and
its lead stage) that don't belong on the global Contact.

A unique constraint on (exhibition_id, contact_id) is what makes "the
same Contact already linked to the same Exhibition" a true, DB-enforced
duplicate, while the same Contact linked to two different Exhibitions
is two perfectly valid rows.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ExhibitionContact(Base):
    __tablename__ = "exhibition_contacts"
    __table_args__ = (
        UniqueConstraint("exhibition_id", "contact_id", name="uq_exhibition_contact"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    exhibition_id: Mapped[int] = mapped_column(
        ForeignKey("exhibitions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[int] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lead_stage_id: Mapped[int | None] = mapped_column(
        ForeignKey("lead_stages.id", ondelete="SET NULL"), nullable=True
    )

    stand_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Where this participant/link came from, e.g. "Import: exhibitors.xlsx"
    # or "Manual". Free text, deliberately not another entity for this
    # milestone.
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    exhibition: Mapped["Exhibition"] = relationship(back_populates="participants")
    contact: Mapped["Contact"] = relationship(back_populates="exhibition_links")
    lead_stage: Mapped["LeadStage | None"] = relationship(back_populates="exhibition_contacts")

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"<ExhibitionContact id={self.id} exhibition_id={self.exhibition_id} contact_id={self.contact_id}>"
