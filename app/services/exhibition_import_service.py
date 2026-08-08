"""
Exhibition-scoped import service.

Extends the existing Excel/CSV import capability (same file reading,
column-alias detection, and email validation as
`ContactImportExportService`) to import participants *into a selected
Exhibition* instead of the flat, unscoped Contact list.

`Contact` stays the single global identity, deduplicated by email --
this service never creates a second Contact for an email that already
exists. Every row is classified into exactly one of five buckets:

    - new_contact   -- email not seen anywhere before; a new global
                       Contact will be created AND linked to the
                       selected Exhibition.
    - link_existing -- a global Contact with this email already
                       exists, but is NOT yet linked to the selected
                       Exhibition; the existing Contact is reused and
                       only a new ExhibitionContact link is created.
    - duplicate     -- a TRUE exhibition duplicate: either an existing
                       Contact that is ALREADY linked to this exact
                       Exhibition, or the same new email repeated twice
                       within the file itself.
    - invalid       -- an email value is present but not well-formed.
    - skipped       -- no email at all in the row.

`analyze_file()` / `commit_import()` are two separate steps, same as
the Contact importer, so the UI can preview before anything is written.
This module does not touch `ContactImportExportService` at all -- the
original Contact import path is completely unaffected by this file's
existence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import pandas as pd

from app.config.constants import CONTACT_IMPORT_COLUMN_ALIASES
from app.models.contact import Contact
from app.models.exhibition_contact import ExhibitionContact
from app.repositories.contact_repository import ContactRepository
from app.repositories.exhibition_contact_repository import ExhibitionContactRepository
from app.repositories.lead_stage_repository import LeadStageRepository
from app.utils.validators import is_valid_email, normalize_email

logger = logging.getLogger(__name__)

RowStatus = Literal["new_contact", "link_existing", "duplicate", "invalid", "skipped"]

SUPPORTED_IMPORT_EXTENSIONS = (".xlsx", ".xls", ".csv")

CANONICAL_FIELDS: tuple[str, ...] = (
    "email", "contact_name", "company", "country", "website", "phone", "stand_number", "notes",
)
REQUIRED_CANONICAL_FIELDS: tuple[str, ...] = ("email",)


@dataclass(frozen=True)
class ExhibitionImportRow:
    """One row from the imported file, already mapped and classified."""

    row_number: int  # 1-based, matches the spreadsheet row the user sees
    status: RowStatus
    reason: str
    email: str
    contact_name: str
    company: str
    country: str
    website: str
    phone: str
    stand_number: str
    notes: str
    existing_contact_id: int | None = None


@dataclass
class ExhibitionImportPreview:
    """Full result of analyzing a file against one Exhibition, ready to render."""

    exhibition_id: int
    file_path: Path
    rows: list[ExhibitionImportRow] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.rows)

    @property
    def new_contact_count(self) -> int:
        return sum(1 for row in self.rows if row.status == "new_contact")

    @property
    def link_existing_count(self) -> int:
        return sum(1 for row in self.rows if row.status == "link_existing")

    @property
    def duplicate_count(self) -> int:
        return sum(1 for row in self.rows if row.status == "duplicate")

    @property
    def invalid_count(self) -> int:
        return sum(1 for row in self.rows if row.status == "invalid")

    @property
    def skipped_count(self) -> int:
        return sum(1 for row in self.rows if row.status == "skipped")


@dataclass(frozen=True)
class ExhibitionImportSummary:
    new_contacts_created: int
    links_created: int
    duplicates: int
    invalid: int
    skipped: int


class ExhibitionImportService:
    def __init__(
        self,
        contact_repository: ContactRepository | None = None,
        exhibition_contact_repository: ExhibitionContactRepository | None = None,
        lead_stage_repository: LeadStageRepository | None = None,
    ) -> None:
        self._contact_repository = contact_repository or ContactRepository()
        self._exhibition_contact_repository = exhibition_contact_repository or ExhibitionContactRepository()
        self._lead_stage_repository = lead_stage_repository or LeadStageRepository()

    # ------------------------------------------------------------------
    # Column mapping (same alias table/behavior as the Contact importer)
    # ------------------------------------------------------------------
    def get_file_headers(self, file_path: str | Path) -> list[str]:
        dataframe = self._read_dataframe(Path(file_path))
        return [str(column) for column in dataframe.columns]

    def detect_auto_mapping(self, file_path: str | Path) -> dict[str, str]:
        headers = self.get_file_headers(file_path)
        mapping: dict[str, str] = {}
        for header in headers:
            normalized = str(header).strip().lower()
            canonical = CONTACT_IMPORT_COLUMN_ALIASES.get(normalized)
            if canonical:
                mapping[header] = canonical
        return mapping

    @staticmethod
    def is_mapping_complete(mapping: dict[str, str]) -> bool:
        mapped_canonical_fields = set(mapping.values())
        return all(field_name in mapped_canonical_fields for field_name in REQUIRED_CANONICAL_FIELDS)

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------
    def analyze_file(
        self,
        file_path: str | Path,
        exhibition_id: int,
        manual_mapping: dict[str, str] | None = None,
    ) -> ExhibitionImportPreview:
        path = Path(file_path)
        if path.suffix.lower() not in SUPPORTED_IMPORT_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{path.suffix}'. Expected one of {SUPPORTED_IMPORT_EXTENSIONS}."
            )

        dataframe = self._read_dataframe(path)
        mapped = self._map_columns(dataframe, manual_mapping)

        raw_emails = [self._safe_str(v) for v in mapped.get("email", pd.Series(dtype=str)).tolist()]
        candidate_emails = [
            normalize_email(e) for e in raw_emails if e and is_valid_email(e)
        ]

        existing_contact_ids_by_email = self._contact_repository.get_contact_ids_by_emails(candidate_emails)
        linked_contact_ids = self._exhibition_contact_repository.get_linked_contact_ids(exhibition_id)

        seen_new_emails_in_file: set[str] = set()

        preview = ExhibitionImportPreview(exhibition_id=exhibition_id, file_path=path)
        for position, row in enumerate(mapped.to_dict(orient="records"), start=1):
            preview.rows.append(
                self._classify_row(
                    position, row, existing_contact_ids_by_email, linked_contact_ids, seen_new_emails_in_file
                )
            )

        logger.info(
            "Analyzed exhibition import file %s for exhibition_id=%s: "
            "%d new, %d link-existing, %d duplicate, %d invalid, %d skipped",
            path.name, exhibition_id,
            preview.new_contact_count, preview.link_existing_count,
            preview.duplicate_count, preview.invalid_count, preview.skipped_count,
        )
        return preview

    # ------------------------------------------------------------------
    # Commit
    # ------------------------------------------------------------------
    def commit_import(self, preview: ExhibitionImportPreview) -> ExhibitionImportSummary:
        """Create any brand-new Contacts, then link every valid row's Contact
        (new or reused) to the Exhibition. Duplicate/invalid/skipped rows are
        never written.
        """
        default_stage = self._lead_stage_repository.get_default()
        default_stage_id = default_stage.id if default_stage else None
        source_label = f"Import: {preview.file_path.name}"

        new_contact_rows = [row for row in preview.rows if row.status == "new_contact"]
        link_existing_rows = [row for row in preview.rows if row.status == "link_existing"]

        new_contacts = [
            Contact(
                email=row.email,
                contact_name=row.contact_name or None,
                company=row.company or None,
                country=row.country or None,
                website=row.website or None,
                phone=row.phone or None,
                notes=row.notes or None,
            )
            for row in new_contact_rows
        ]
        # bulk_add flushes within its own session, which populates each
        # Contact instance's .id in place (expire_on_commit=False keeps
        # it readable afterward) -- so `new_contacts` can be zipped back
        # against `new_contact_rows` below without a second query.
        self._contact_repository.bulk_add(new_contacts)

        links: list[ExhibitionContact] = []
        for row, contact in zip(new_contact_rows, new_contacts):
            links.append(
                ExhibitionContact(
                    exhibition_id=preview.exhibition_id,
                    contact_id=contact.id,
                    stand_number=row.stand_number or None,
                    source=source_label,
                    lead_stage_id=default_stage_id,
                )
            )
        for row in link_existing_rows:
            links.append(
                ExhibitionContact(
                    exhibition_id=preview.exhibition_id,
                    contact_id=row.existing_contact_id,
                    stand_number=row.stand_number or None,
                    source=source_label,
                    lead_stage_id=default_stage_id,
                )
            )

        links_created = self._exhibition_contact_repository.bulk_add(links)

        summary = ExhibitionImportSummary(
            new_contacts_created=len(new_contacts),
            links_created=links_created,
            duplicates=preview.duplicate_count,
            invalid=preview.invalid_count,
            skipped=preview.skipped_count,
        )
        logger.info("Exhibition import committed: exhibition_id=%s %s", preview.exhibition_id, summary)
        return summary

    # ------------------------------------------------------------------
    # Internal helpers (same behavior as ContactImportExportService)
    # ------------------------------------------------------------------
    def _read_dataframe(self, path: Path) -> pd.DataFrame:
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path, dtype=str, keep_default_na=False)
        return pd.read_excel(path, dtype=str)

    def _map_columns(
        self, dataframe: pd.DataFrame, manual_mapping: dict[str, str] | None = None
    ) -> pd.DataFrame:
        manual_mapping = manual_mapping or {}
        rename_map: dict[str, str] = {}
        for original_column in dataframe.columns:
            if original_column in manual_mapping:
                rename_map[original_column] = manual_mapping[original_column]
                continue
            normalized = str(original_column).strip().lower()
            canonical = CONTACT_IMPORT_COLUMN_ALIASES.get(normalized)
            if canonical:
                rename_map[original_column] = canonical

        renamed = dataframe.rename(columns=rename_map)
        for field_name in CANONICAL_FIELDS:
            if field_name not in renamed.columns:
                renamed[field_name] = ""
        return renamed

    def _classify_row(
        self,
        row_number: int,
        row: dict,
        existing_contact_ids_by_email: dict[str, int],
        linked_contact_ids: set[int],
        seen_new_emails_in_file: set[str],
    ) -> ExhibitionImportRow:
        raw_email = self._safe_str(row.get("email"))
        contact_name = self._safe_str(row.get("contact_name"))
        company = self._safe_str(row.get("company"))
        country = self._safe_str(row.get("country"))
        website = self._safe_str(row.get("website"))
        phone = self._safe_str(row.get("phone"))
        stand_number = self._safe_str(row.get("stand_number"))
        notes = self._safe_str(row.get("notes"))

        if not raw_email:
            return ExhibitionImportRow(
                row_number, "skipped", "Empty email", "", contact_name, company,
                country, website, phone, stand_number, notes,
            )

        if not is_valid_email(raw_email):
            return ExhibitionImportRow(
                row_number, "invalid", "Malformed email address", raw_email, contact_name,
                company, country, website, phone, stand_number, notes,
            )

        email = normalize_email(raw_email)
        existing_contact_id = existing_contact_ids_by_email.get(email)

        if existing_contact_id is not None:
            if existing_contact_id in linked_contact_ids:
                return ExhibitionImportRow(
                    row_number, "duplicate", "Already linked to this exhibition", email,
                    contact_name, company, country, website, phone, stand_number, notes,
                    existing_contact_id=existing_contact_id,
                )
            return ExhibitionImportRow(
                row_number, "link_existing", "Existing contact -- will be linked", email,
                contact_name, company, country, website, phone, stand_number, notes,
                existing_contact_id=existing_contact_id,
            )

        if email in seen_new_emails_in_file:
            return ExhibitionImportRow(
                row_number, "duplicate", "Duplicate email within this file", email,
                contact_name, company, country, website, phone, stand_number, notes,
            )

        seen_new_emails_in_file.add(email)
        return ExhibitionImportRow(
            row_number, "new_contact", "", email, contact_name, company, country,
            website, phone, stand_number, notes,
        )

    @staticmethod
    def _safe_str(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, float) and pd.isna(value):
            return ""
        text = str(value).strip()
        return "" if text.lower() == "nan" else text
