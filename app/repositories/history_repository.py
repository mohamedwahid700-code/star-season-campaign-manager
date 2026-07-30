"""Repository for `History` records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import joinedload

from app.database.base import session_scope
from app.models.history import DeliveryStatus, History
from app.repositories.base_repository import BaseRepository


@dataclass(frozen=True)
class HistoryDetail:
    """
    Flat, already-detached view of a `History` row plus the campaign/
    contact fields the History page displays. Built from the ORM
    relationships *while the session is still open* in
    `get_all_details()`, so the page never needs to touch a lazy
    relationship on an object whose session has already closed.
    """

    id: int
    company: str
    contact_name: str
    email: str
    campaign_name: str
    status: DeliveryStatus
    sent_at: datetime | None
    created_at: datetime
    error_message: str


class HistoryRepository(BaseRepository[History]):
    def __init__(self) -> None:
        super().__init__(History)

    def get_by_campaign(self, campaign_id: int) -> list[History]:
        with session_scope() as session:
            return session.query(History).filter(History.campaign_id == campaign_id).all()

    def get_by_status(self, status: DeliveryStatus) -> list[History]:
        with session_scope() as session:
            return session.query(History).filter(History.status == status).all()

    def get_all_details(self) -> list[HistoryDetail]:
        """Every History row, newest first, with campaign/contact fields flattened for display."""
        with session_scope() as session:
            rows = (
                session.query(History)
                .options(joinedload(History.campaign), joinedload(History.contact))
                .order_by(History.created_at.desc())
                .all()
            )
            return [
                HistoryDetail(
                    id=row.id,
                    company=(row.contact.company or "") if row.contact else "",
                    contact_name=(row.contact.display_name if row.contact else ""),
                    email=(row.contact.email if row.contact else ""),
                    campaign_name=(row.campaign.name if row.campaign else ""),
                    status=row.status,
                    sent_at=row.sent_at,
                    created_at=row.created_at,
                    error_message=row.error_message or "",
                )
                for row in rows
            ]
