"""History model.

Represents a single audit record of an email that was (or was attempted
to be) sent as part of a campaign, to a specific contact. Sprint 3 is
the first to actually write rows here: every Outlook "Send Test Email"
attempt is logged, regardless of outcome, via `SendLogService`. Bulk
sending / a real send queue remain out of scope for this sprint.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class History(Base):
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[int] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status"),
        default=DeliveryStatus.PENDING,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # The Outlook account (SMTP address) the message was sent/attempted
    # from. Nullable so any future non-Outlook sending path still fits
    # this same audit table without another migration.
    sender_account: Mapped[str | None] = mapped_column(String(255), nullable=True)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    campaign: Mapped["Campaign"] = relationship(back_populates="history_entries")
    contact: Mapped["Contact"] = relationship(back_populates="history_entries")

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"<History id={self.id} campaign_id={self.campaign_id} status={self.status.value}>"
