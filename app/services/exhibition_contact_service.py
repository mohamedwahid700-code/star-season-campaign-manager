"""
ExhibitionContact service.

Reads the participant list for a given Exhibition, and links a single
already-known Contact to an Exhibition by hand (the bulk/import path
lives in `ExhibitionImportService`, which has its own preview/commit
semantics). Every new link lands in the seeded default `LeadStage`
("New") unless told otherwise.
"""

from __future__ import annotations

import logging

from app.models.exhibition_contact import ExhibitionContact
from app.repositories.exhibition_contact_repository import (
    ExhibitionContactRepository,
    ExhibitionParticipant,
)
from app.repositories.lead_stage_repository import LeadStageRepository

logger = logging.getLogger(__name__)


class DuplicateExhibitionContactError(ValueError):
    """Raised when a Contact is already linked to the target Exhibition."""


class ExhibitionContactService:
    def __init__(
        self,
        repository: ExhibitionContactRepository | None = None,
        lead_stage_repository: LeadStageRepository | None = None,
    ) -> None:
        self._repository = repository or ExhibitionContactRepository()
        self._lead_stage_repository = lead_stage_repository or LeadStageRepository()

    def get_participants(self, exhibition_id: int) -> list[ExhibitionParticipant]:
        """Every Contact currently linked to `exhibition_id`, ready for display or

        for a future campaign send to draw its recipient list from.
        """
        return self._repository.get_participants(exhibition_id)

    def count_for_exhibition(self, exhibition_id: int) -> int:
        return self._repository.count_for_exhibition(exhibition_id)

    def link_contact(
        self,
        exhibition_id: int,
        contact_id: int,
        stand_number: str = "",
        source: str = "Manual",
    ) -> ExhibitionContact:
        """Link an existing global Contact to an Exhibition.

        Raises `DuplicateExhibitionContactError` if this exact
        Contact/Exhibition pair is already linked -- that is the only
        thing that counts as a true exhibition duplicate.
        """
        existing = self._repository.get_link(exhibition_id, contact_id)
        if existing is not None:
            raise DuplicateExhibitionContactError(
                f"Contact id={contact_id} is already linked to exhibition id={exhibition_id}."
            )

        default_stage = self._lead_stage_repository.get_default()

        link = ExhibitionContact(
            exhibition_id=exhibition_id,
            contact_id=contact_id,
            stand_number=stand_number.strip() or None,
            source=source.strip() or None,
            lead_stage_id=default_stage.id if default_stage else None,
        )
        created = self._repository.add(link)
        logger.info(
            "ExhibitionContact linked: exhibition_id=%s contact_id=%s", exhibition_id, contact_id
        )
        return created
