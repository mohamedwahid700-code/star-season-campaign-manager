"""Repository for `ExhibitionContact` records.

Every read that the UI displays comes back as a flat, already-detached
`ExhibitionParticipant` (built from the ORM relationships while the
session is still open), the same pattern `HistoryRepository.get_all_details()`
already uses -- so callers never need to touch a lazy relationship on an
object whose session has closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import joinedload

from app.database.base import session_scope
from app.models.exhibition_contact import ExhibitionContact
from app.repositories.base_repository import BaseRepository


@dataclass(frozen=True)
class ExhibitionParticipant:
    """Flat view of one ExhibitionContact row plus its Contact fields, for display."""

    id: int
    exhibition_id: int
    contact_id: int
    contact_name: str
    company: str
    email: str
    country: str
    stand_number: str
    source: str
    lead_stage_name: str
    created_at: datetime


class ExhibitionContactRepository(BaseRepository[ExhibitionContact]):
    def __init__(self) -> None:
        super().__init__(ExhibitionContact)

    def get_link(self, exhibition_id: int, contact_id: int) -> ExhibitionContact | None:
        """Return the existing link between this Exhibition and this Contact, if any.

        This is the single source of truth for "is this Contact already
        an exhibition duplicate for this Exhibition?" -- a row here means
        yes, no row means the Contact (if it exists globally) can simply
        be linked.
        """
        with session_scope() as session:
            return (
                session.query(ExhibitionContact)
                .filter(
                    ExhibitionContact.exhibition_id == exhibition_id,
                    ExhibitionContact.contact_id == contact_id,
                )
                .first()
            )

    def get_linked_contact_ids(self, exhibition_id: int) -> set[int]:
        """Every contact_id already linked to this Exhibition, in one query."""
        with session_scope() as session:
            rows = (
                session.query(ExhibitionContact.contact_id)
                .filter(ExhibitionContact.exhibition_id == exhibition_id)
                .all()
            )
            return {row.contact_id for row in rows}

    def bulk_add(self, links: list[ExhibitionContact]) -> int:
        """Insert many exhibition-contact links in a single transaction."""
        if not links:
            return 0
        with session_scope() as session:
            session.add_all(links)
            session.flush()
            return len(links)

    def get_participants(self, exhibition_id: int) -> list[ExhibitionParticipant]:
        """Every participant linked to `exhibition_id`, newest first, ready to display."""
        with session_scope() as session:
            rows = (
                session.query(ExhibitionContact)
                .options(
                    joinedload(ExhibitionContact.contact),
                    joinedload(ExhibitionContact.lead_stage),
                )
                .filter(ExhibitionContact.exhibition_id == exhibition_id)
                .order_by(ExhibitionContact.created_at.desc())
                .all()
            )
            return [
                ExhibitionParticipant(
                    id=row.id,
                    exhibition_id=row.exhibition_id,
                    contact_id=row.contact_id,
                    contact_name=(row.contact.display_name if row.contact else ""),
                    company=(row.contact.company or "") if row.contact else "",
                    email=(row.contact.email if row.contact else ""),
                    country=(row.contact.country or "") if row.contact else "",
                    stand_number=row.stand_number or "",
                    source=row.source or "",
                    lead_stage_name=(row.lead_stage.name if row.lead_stage else ""),
                    created_at=row.created_at,
                )
                for row in rows
            ]

    def count_for_exhibition(self, exhibition_id: int) -> int:
        with session_scope() as session:
            return (
                session.query(ExhibitionContact)
                .filter(ExhibitionContact.exhibition_id == exhibition_id)
                .count()
            )
