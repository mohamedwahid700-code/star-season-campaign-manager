"""
Exhibition controller.

Mediates between the Exhibitions page (list + create/edit dialog +
import dialog) and the two services that back it: `ExhibitionService`
for CRUD, and `ExhibitionImportService` for the exhibition-scoped
Excel/CSV import workflow. Views call this controller only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.models.exhibition import Exhibition
from app.services.exhibition_import_service import (
    ExhibitionImportPreview,
    ExhibitionImportService,
    ExhibitionImportSummary,
)
from app.services.exhibition_service import ExhibitionService


@dataclass(frozen=True)
class ExhibitionFormData:
    """Plain data captured from the Add/Edit Exhibition dialog."""

    name: str
    location: str = ""
    start_date: datetime | None = None
    end_date: datetime | None = None
    notes: str = ""


class ExhibitionController:
    def __init__(
        self,
        exhibition_service: ExhibitionService | None = None,
        import_service: ExhibitionImportService | None = None,
    ) -> None:
        self._exhibition_service = exhibition_service or ExhibitionService()
        self._import_service = import_service or ExhibitionImportService()

    # ------------------------------------------------------------------
    # CRUD / listing
    # ------------------------------------------------------------------
    def list_exhibitions(self) -> list[Exhibition]:
        return self._exhibition_service.list_exhibitions()

    def get_exhibition(self, exhibition_id: int) -> Exhibition | None:
        return self._exhibition_service.get_exhibition(exhibition_id)

    def create_exhibition(self, data: ExhibitionFormData) -> Exhibition:
        return self._exhibition_service.create_exhibition(
            name=data.name, location=data.location,
            start_date=data.start_date, end_date=data.end_date, notes=data.notes,
        )

    def update_exhibition(self, exhibition_id: int, data: ExhibitionFormData) -> Exhibition:
        return self._exhibition_service.update_exhibition(
            exhibition_id, name=data.name, location=data.location,
            start_date=data.start_date, end_date=data.end_date, notes=data.notes,
        )

    # ------------------------------------------------------------------
    # Exhibition-scoped import
    # ------------------------------------------------------------------
    def get_file_headers(self, file_path: str) -> list[str]:
        return self._import_service.get_file_headers(file_path)

    def detect_column_mapping(self, file_path: str) -> dict[str, str]:
        return self._import_service.detect_auto_mapping(file_path)

    def is_column_mapping_complete(self, mapping: dict[str, str]) -> bool:
        return self._import_service.is_mapping_complete(mapping)

    def analyze_import_file(
        self, file_path: str, exhibition_id: int, manual_mapping: dict[str, str] | None = None
    ) -> ExhibitionImportPreview:
        return self._import_service.analyze_file(file_path, exhibition_id, manual_mapping)

    def commit_import(self, preview: ExhibitionImportPreview) -> ExhibitionImportSummary:
        return self._import_service.commit_import(preview)
