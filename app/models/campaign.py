"""Campaign model.

Represents an email campaign sent to exhibition participants. Sprint 2
adds the fields needed to author a campaign's own content directly
(event name, language, subject, HTML body) so that editing the shared
Template library later does not retroactively change a campaign that
already copied its content from a template. Sending logic (Outlook,
queueing, delays) still arrives in a later sprint.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    event_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # The real, first-class relationship a campaign's recipients are
    # resolved through (via ExhibitionContact). `event_name` above is
    # legacy free text and is no longer the primary link -- it is kept
    # only so existing campaigns/history stay readable. Nullable so
    # older campaigns created before this field existed keep loading
    # normally and fall back to the legacy "All Contacts" recipient
    # flow.
    exhibition_id: Mapped[int | None] = mapped_column(
        ForeignKey("exhibitions.id", ondelete="SET NULL"), nullable=True
    )

    language: Mapped[str] = mapped_column(String(50), nullable=False, default="English")
    subject: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    html_body: Mapped[str] = mapped_column(Text, nullable=False, default="")

    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status"),
        default=CampaignStatus.DRAFT,
        nullable=False,
    )

    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("templates.id", ondelete="SET NULL"), nullable=True
    )

    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    template: Mapped["Template | None"] = relationship(back_populates="campaigns")
    history_entries: Mapped[list["History"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    # One-directional: Exhibition does not need a `campaigns` back-reference
    # for this milestone, so its model is left untouched.
    exhibition: Mapped["Exhibition | None"] = relationship(viewonly=False)

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"<Campaign id={self.id} name={self.name!r} status={self.status.value}>"
