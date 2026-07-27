"""
Contact import/export service.

Reads an Excel (.xlsx) or CSV (.csv) file with `pandas`, maps whatever
column headers the file happens to use onto the `Contact` model's
fields via `CONTACT_IMPORT_COLUMN_ALIASES`, and classifies every row
into exactly one of four buckets so the UI can show the same counters
the business asked for:

    - Imported  -- valid, non-duplicate email; will be inserted
    - Skipped   -- no email at all in the row
    - Invalid   -- an email value is present but not well-formed
    - Duplicate -- valid email, but it already exists (in the file
                   itself or already in the database)

`analyze_file()` and `commit_import()` are deliberately two separate
steps so the UI can show a preview and let the user confirm before
anything is written to the database.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import pandas as pd

from app.config.constants import CONTACT_EXPORT_COLUMNS, CONTACT_IMPORT_COLUMN_ALIASES
from app.models.contact import Contact
from app.repositories.contact_repository import ContactRepository
from app.utils.validators import is_valid_email, normalize_email

logger = logging.getLogger(__name__)

RowStatus = Literal["valid", "skipped", "invalid", "duplicate"]

SUPPORTED_IMPORT_EXTENSIONS = (".xlsx", ".xls", ".csv")
SUPPORTED_EXPORT_EXTENSIONS = (".xlsx", ".csv")

# Every canonical Contact field the importer understands, and which of
# them absolutely must be mapped to something before an import can
# proceed (only email -- everything else is optional metadata).
CANONICAL_FIELDS: tuple[str, ...] = (
    "email", "contact_name", "company", "country", "website", "phone", "stand_number", "notes",
)
REQUIRED_CANONICAL_FIELDS: tuple[str, ...] = ("email",)


@dataclass(frozen=True)
class ImportRow:
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


@dataclass
class ImportPreview:
    """Full result of analyzing a file, ready to render as a preview table."""

    file_path: Path
    rows: list[ImportRow] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.rows)

    @property
    def valid_count(self) -> int:
        return sum(1 for row in self.rows if row.status == "valid")

    @property
    def skipped_count(self) -> int:
        return sum(1 for row in self.rows if row.status == "skipped")

    @property
    def invalid_count(self) -> int:
        return sum(1 for row in self.rows if row.status == "invalid")

    @property
    def duplicate_count(self) -> int:
        return sum(1 for row in self.rows if row.status == "duplicate")


@dataclass(frozen=True)
class ImportSummary:
    imported: int
    skipped: int
    invalid: int
    duplicates: int


class ContactImportExportService:
    def __init__(self, repository: ContactRepository | None = None) -> None:
        self._repository = repository or ContactRepository()

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------
    def get_file_headers(self, file_path: str | Path) -> list[str]:
        """Return the raw column headers of `file_path`, for the mapping dialog."""
        path = Path(file_path)
        dataframe = self._read_dataframe(path)
        return [str(column) for column in dataframe.columns]

    def detect_auto_mapping(self, file_path: str | Path) -> dict[str, str]:
        """
        Return the raw-header -> canonical-field mapping the built-in
        alias table can resolve automatically, without touching any
        rows. Used to decide whether the manual mapping dialog needs to
        be shown (i.e. a required field like email wasn't detected).
        """
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
        """True once every required canonical field (currently just email) is covered."""
        mapped_canonical_fields = set(mapping.values())
        return all(field_name in mapped_canonical_fields for field_name in REQUIRED_CANONICAL_FIELDS)

    def analyze_file(
        self, file_path: str | Path, manual_mapping: dict[str, str] | None = None
    ) -> ImportPreview:
        """
        Parse and classify every row of `file_path` without writing anything.

        `manual_mapping` (raw header -> canonical field) takes priority
        over the built-in alias table for any header it covers, letting
        a user-confirmed mapping override an ambiguous or unrecognized
        column name.
        """
        path = Path(file_path)
        if path.suffix.lower() not in SUPPORTED_IMPORT_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{path.suffix}'. Expected one of {SUPPORTED_IMPORT_EXTENSIONS}."
            )

        dataframe = self._read_dataframe(path)
        mapped = self._map_columns(dataframe, manual_mapping)

        existing_emails = self._repository.get_existing_emails(
            [self._safe_str(v) for v in mapped.get("email", pd.Series(dtype=str)).tolist()]
        )
        seen_in_file: set[str] = set()

        preview = ImportPreview(file_path=path)
        for position, row in enumerate(mapped.to_dict(orient="records"), start=1):
            preview.rows.append(
                self._classify_row(position, row, existing_emails, seen_in_file)
            )

        logger.info(
            "Analyzed import file %s: %d valid, %d skipped, %d invalid, %d duplicate",
            path.name,
            preview.valid_count,
            preview.skipped_count,
            preview.invalid_count,
            preview.duplicate_count,
        )
        return preview

    def commit_import(self, preview: ImportPreview) -> ImportSummary:
        """Insert every `valid` row from a previously-analyzed preview."""
        contacts_to_insert = [
            Contact(
                email=row.email,
                contact_name=row.contact_name or None,
                company=row.company or None,
                country=row.country or None,
                website=row.website or None,
                phone=row.phone or None,
                stand_number=row.stand_number or None,
                notes=row.notes or None,
            )
            for row in preview.rows
            if row.status == "valid"
        ]
        imported = self._repository.bulk_add(contacts_to_insert)
        summary = ImportSummary(
            imported=imported,
            skipped=preview.skipped_count,
            invalid=preview.invalid_count,
            duplicates=preview.duplicate_count,
        )
        logger.info("Import committed: %s", summary)
        return summary

    def _read_dataframe(self, path: Path) -> pd.DataFrame:
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path, dtype=str, keep_default_na=False)
        return pd.read_excel(path, dtype=str)

    def _map_columns(
        self, dataframe: pd.DataFrame, manual_mapping: dict[str, str] | None = None
    ) -> pd.DataFrame:
        """Rename whatever headers the file uses onto our canonical field names.

        A user-provided `manual_mapping` (raw header -> canonical field)
        takes priority; any column it doesn't cover falls back to the
        built-in alias table.
        """
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

        # Ensure every field we care about exists as a column, even if the
        # source file didn't include it, so downstream code never has to
        # special-case a missing key.
        for field_name in CANONICAL_FIELDS:
            if field_name not in renamed.columns:
                renamed[field_name] = ""

        return renamed

    def _classify_row(
        self,
        row_number: int,
        row: dict,
        existing_emails: set[str],
        seen_in_file: set[str],
    ) -> ImportRow:
        raw_email = self._safe_str(row.get("email"))
        contact_name = self._safe_str(row.get("contact_name"))
        company = self._safe_str(row.get("company"))
        country = self._safe_str(row.get("country"))
        website = self._safe_str(row.get("website"))
        phone = self._safe_str(row.get("phone"))
        stand_number = self._safe_str(row.get("stand_number"))
        notes = self._safe_str(row.get("notes"))

        if not raw_email:
            return ImportRow(
                row_number, "skipped", "Empty email", "", contact_name, company,
                country, website, phone, stand_number, notes,
            )

        if not is_valid_email(raw_email):
            return ImportRow(
                row_number, "invalid", "Malformed email address", raw_email, contact_name,
                company, country, website, phone, stand_number, notes,
            )

        email = normalize_email(raw_email)

        if email in existing_emails or email in seen_in_file:
            return ImportRow(
                row_number, "duplicate", "Email already exists", email, contact_name,
                company, country, website, phone, stand_number, notes,
            )

        seen_in_file.add(email)
        return ImportRow(
            row_number, "valid", "", email, contact_name, company, country,
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

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export_contacts(self, contacts: list[Contact], file_path: str | Path) -> Path:
        """Write `contacts` out to `file_path` as .xlsx or .csv, inferred from the extension."""
        path = Path(file_path)
        if path.suffix.lower() not in SUPPORTED_EXPORT_EXTENSIONS:
            raise ValueError(
                f"Unsupported export type '{path.suffix}'. Expected one of {SUPPORTED_EXPORT_EXTENSIONS}."
            )

        records = [
            {label: getattr(contact, field_name) or "" for field_name, label in CONTACT_EXPORT_COLUMNS}
            for contact in contacts
        ]
        dataframe = pd.DataFrame.from_records(
            records, columns=[label for _, label in CONTACT_EXPORT_COLUMNS]
        )

        if path.suffix.lower() == ".csv":
            dataframe.to_csv(path, index=False)
        else:
            dataframe.to_excel(path, index=False)

        logger.info("Exported %d contact(s) to %s", len(contacts), path)
        return path
