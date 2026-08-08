"""
ExhibitionContact controller.

Mediates between the UI (Exhibitions page's participant panel, and any
future campaign recipient picker) and `ExhibitionContactService`. Views
must never call the service or repository directly.
"""

from __future__ import annotations

from app.repositories.exhibition_contact_repository import ExhibitionParticipant
from app.services.exhibition_contact_service import ExhibitionContactService


class ExhibitionContactController:
    def __init__(self, exhibition_contact_service: ExhibitionContactService | None = None) -> None:
        self._service = exhibition_contact_service or ExhibitionContactService()

    def get_participants(self, exhibition_id: int) -> list[ExhibitionParticipant]:
        """The linked participants for `exhibition_id`, ready to display --

        and, going forward, the same list a campaign send would draw its
        exhibition-scoped recipients from.
        """
        return self._service.get_participants(exhibition_id)

    def count_for_exhibition(self, exhibition_id: int) -> int:
        return self._service.count_for_exhibition(exhibition_id)
