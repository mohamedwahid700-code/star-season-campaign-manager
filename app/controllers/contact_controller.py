"""
Contact controller.

Mediates between the Contacts page and the two services that back it:
`ContactService` for CRUD + search/sort/filter, and
`ContactImportExportService` for the Excel/CSV import/export workflow.
Views call this controller only; they never import a service directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models.contact import Contact
from app.services.contact_import_export_service import (
    ContactImportExportService,
    ImportPreview,
    ImportSummary,
)
from app.services.contact_service import ContactService
from app.services.settings_service import SettingsService


@dataclass(frozen=True)
class ContactFormData:
    """Plain data captured from the Add/Edit Contact dialog."""

    email: str
    contact_name: str = ""
    company: str = ""
    country: str = ""
    website: str = ""
    phone: str = ""
    stand_number: str = ""
    notes: str = ""


class ContactController:
    def __init__(
        self,
        contact_service: ContactService | None = None,
        import_export_service: ContactImportExportService | None = None,
        settings_service: SettingsService | None = None,
    ) -> None:
        self._contact_service = contact_service or ContactService()
        self._import_export_service = import_export_service or ContactImportExportService()
        self._settings_service = settings_service or SettingsService()

    # ------------------------------------------------------------------
    # Listing / search / filter
    # ------------------------------------------------------------------
    def list_contacts(
        self,
        search_term: str = "",
        country: str = "",
        sort_by: str = "updated_at",
        sort_descending: bool = True,
    ) -> list[Contact]:
        return self._contact_service.list_contacts(
            search_term=search_term.strip() or None,
            country=country.strip() or None,
            sort_by=sort_by,
            sort_descending=sort_descending,
        )

    def get_countries(self) -> list[str]:
        return self._contact_service.get_countries()

    def get_contact(self, contact_id: int) -> Contact | None:
        return self._contact_service.get_contact(contact_id)

    # ------------------------------------------------------------------
    # Create / edit / delete
    # ------------------------------------------------------------------
    def create_contact(self, data: ContactFormData) -> Contact:
        return self._contact_service.create_contact(
            email=data.email,
            contact_name=data.contact_name,
            company=data.company,
            country=data.country,
            website=data.website,
            phone=data.phone,
            stand_number=data.stand_number,
            notes=data.notes,
        )

    def update_contact(self, contact_id: int, data: ContactFormData) -> Contact:
        return self._contact_service.update_contact(
            contact_id,
            email=data.email,
            contact_name=data.contact_name,
            company=data.company,
            country=data.country,
            website=data.website,
            phone=data.phone,
            stand_number=data.stand_number,
            notes=data.notes,
        )

    def delete_contact(self, contact_id: int) -> bool:
        return self._contact_service.delete_contact(contact_id)

    # ------------------------------------------------------------------
    # Import / export
    # ------------------------------------------------------------------
    def get_file_headers(self, file_path: str) -> list[str]:
        return self._import_export_service.get_file_headers(file_path)

    def detect_column_mapping(self, file_path: str) -> dict[str, str]:
        """
        Return the best-known raw-header -> canonical-field mapping for
        `file_path`: the built-in alias table's guesses, with any
        previously-remembered manual mapping layered on top (so a header
        the user mapped by hand before is recognized automatically here
        on out).
        """
        auto_mapping = self._import_export_service.detect_auto_mapping(file_path)
        remembered = self._settings_service.get_contact_import_column_mapping()

        headers = set(self._import_export_service.get_file_headers(file_path))
        merged = dict(auto_mapping)
        for header, canonical_field in remembered.items():
            if header in headers:
                merged[header] = canonical_field
        return merged

    def is_column_mapping_complete(self, mapping: dict[str, str]) -> bool:
        return self._import_export_service.is_mapping_complete(mapping)

    def remember_column_mapping(self, mapping: dict[str, str]) -> None:
        """Persist a manually-confirmed mapping so future imports recognize it automatically."""
        existing = self._settings_service.get_contact_import_column_mapping()
        existing.update(mapping)
        self._settings_service.set_contact_import_column_mapping(existing)

    def analyze_import_file(self, file_path: str, manual_mapping: dict[str, str] | None = None) -> ImportPreview:
        return self._import_export_service.analyze_file(file_path, manual_mapping)

    def commit_import(self, preview: ImportPreview) -> ImportSummary:
        return self._import_export_service.commit_import(preview)

    def export_contacts(self, contacts: list[Contact], file_path: str) -> Path:
        return self._import_export_service.export_contacts(contacts, file_path)
