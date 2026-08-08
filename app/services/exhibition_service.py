"""
Exhibition service.

CRUD orchestration for `Exhibition` -- create/edit/list only, per this
milestone's scope. No delete: an Exhibition is the operational hub
participants and (eventually) campaigns are scoped to, so removing one
is deliberately not part of this milestone.
"""

from __future__ import annotations

import logging
from datetime import datetime

from app.models.exhibition import Exhibition
from app.repositories.exhibition_repository import ExhibitionRepository

logger = logging.getLogger(__name__)


class ExhibitionService:
    def __init__(self, repository: ExhibitionRepository | None = None) -> None:
        self._repository = repository or ExhibitionRepository()

    def list_exhibitions(self) -> list[Exhibition]:
        return self._repository.get_all_ordered()

    def get_exhibition(self, exhibition_id: int) -> Exhibition | None:
        return self._repository.get_by_id(exhibition_id)

    def create_exhibition(
        self,
        name: str,
        location: str = "",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        notes: str = "",
    ) -> Exhibition:
        if not name.strip():
            raise ValueError("Exhibition name is required.")

        exhibition = Exhibition(
            name=name.strip(),
            location=location.strip() or None,
            start_date=start_date,
            end_date=end_date,
            notes=notes.strip() or None,
        )
        created = self._repository.add(exhibition)
        logger.info("Exhibition created: id=%s name=%s", created.id, created.name)
        return created

    def update_exhibition(
        self,
        exhibition_id: int,
        name: str,
        location: str = "",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        notes: str = "",
    ) -> Exhibition:
        if not name.strip():
            raise ValueError("Exhibition name is required.")

        exhibition = self._repository.get_by_id(exhibition_id)
        if exhibition is None:
            raise ValueError(f"Exhibition with id={exhibition_id} does not exist.")

        exhibition.name = name.strip()
        exhibition.location = location.strip() or None
        exhibition.start_date = start_date
        exhibition.end_date = end_date
        exhibition.notes = notes.strip() or None

        updated = self._repository.update(exhibition)
        logger.info("Exhibition updated: id=%s name=%s", updated.id, updated.name)
        return updated
