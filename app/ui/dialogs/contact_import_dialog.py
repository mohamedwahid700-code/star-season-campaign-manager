"""
Contact import dialog.

Two-step flow requested for Sprint 2:

    1. Browse for an Excel (.xlsx) or CSV (.csv) file -> preview every
       row's classification (valid / skipped / invalid / duplicate)
       before anything touches the database.
    2. Confirm -> only the valid rows are inserted, and the same four
       counters are shown as a final summary.
"""

from __future__ import annotations

from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from app.controllers.contact_controller import ContactController
from app.services.contact_import_export_service import ImportPreview
from app.ui.components.data_table import DataTable
from app.ui.dialogs.base_dialog import activate_grab, apply_screen_aware_geometry
from app.ui.dialogs.column_mapping_dialog import ColumnMappingDialog
from app.ui.theme.theme_manager import ThemeManager

_STATUS_LABELS = {
    "valid": "Will Import",
    "skipped": "Skipped (empty email)",
    "invalid": "Invalid Email",
    "duplicate": "Duplicate",
}


class ContactImportDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        contact_controller: ContactController,
        on_imported: Callable[[], None],
    ) -> None:
        super().__init__(master, fg_color=theme_manager.color("background"))
        self._theme = theme_manager
        self._controller = contact_controller
        self._on_imported = on_imported
        self._preview: ImportPreview | None = None

        self.title("Import Contacts")
        self.transient(master)
        apply_screen_aware_geometry(
            self, preferred_width=880, preferred_height=620, min_width=640, min_height=420
        )

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_file_row()
        self._build_summary_row()
        self._build_table()
        self._build_footer()

        self.after(50, self._activate_grab)

    def _activate_grab(self) -> None:
        activate_grab(self)

    def _build_file_row(self) -> None:
        row = ctk.CTkFrame(self, fg_color=self._theme.color("surface"), corner_radius=8)
        row.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        row.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row, text="File", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self._theme.color("text_primary"),
        ).grid(row=0, column=0, sticky="w", padx=(16, 8), pady=14)

        self._file_label = ctk.CTkLabel(
            row, text="No file selected", font=ctk.CTkFont(size=12),
            text_color=self._theme.color("text_secondary"), anchor="w",
        )
        self._file_label.grid(row=0, column=1, sticky="ew", pady=14)

        ctk.CTkButton(
            row, text="Browse...", width=110, height=32, corner_radius=8,
            fg_color=self._theme.color("primary"), hover_color=self._theme.color("primary_hover"),
            text_color=self._theme.color("text_on_primary"),
            command=self._handle_browse,
        ).grid(row=0, column=2, padx=16, pady=14)

    def _build_summary_row(self) -> None:
        self._summary_row = ctk.CTkFrame(self, fg_color="transparent")
        self._summary_row.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        self._summary_labels: dict[str, ctk.CTkLabel] = {}

        summary_items = [
            ("imported", "Imported", "success"),
            ("skipped", "Skipped", "text_secondary"),
            ("invalid", "Invalid", "danger"),
            ("duplicates", "Duplicates", "warning"),
        ]
        for index, (key, title, color_key) in enumerate(summary_items):
            card = ctk.CTkFrame(self._summary_row, fg_color=self._theme.color("surface"), corner_radius=8)
            card.grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 8, 0))
            self._summary_row.columnconfigure(index, weight=1)

            value_label = ctk.CTkLabel(
                card, text="0", font=ctk.CTkFont(size=20, weight="bold"),
                text_color=self._theme.color(color_key),
            )
            value_label.pack(pady=(10, 0))
            ctk.CTkLabel(
                card, text=title, font=ctk.CTkFont(size=11), text_color=self._theme.color("text_secondary"),
            ).pack(pady=(0, 10))
            self._summary_labels[key] = value_label

    def _build_table(self) -> None:
        table_container = ctk.CTkFrame(self, fg_color=self._theme.color("surface"), corner_radius=8)
        table_container.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 8))
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(0, weight=1)

        columns = [
            ("row", "#", 40),
            ("status", "Status", 130),
            ("email", "Email", 200),
            ("contact_name", "Contact Name", 140),
            ("company", "Company", 160),
            ("reason", "Reason", 160),
        ]
        self._table = DataTable(table_container, self._theme, columns)
        self._table.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 16))
        footer.columnconfigure(0, weight=1)

        button_row = ctk.CTkFrame(footer, fg_color="transparent")
        button_row.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            button_row, text="Close", width=100, height=36, corner_radius=8,
            fg_color=self._theme.color("surface_alt"), hover_color=self._theme.color("border"),
            text_color=self._theme.color("text_primary"), command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        self._import_button = ctk.CTkButton(
            button_row, text="Import Contacts", width=150, height=36, corner_radius=8,
            fg_color=self._theme.color("primary"), hover_color=self._theme.color("primary_hover"),
            text_color=self._theme.color("text_on_primary"),
            command=self._handle_commit, state="disabled",
        )
        self._import_button.pack(side="left")

    def _handle_browse(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select Contact File",
            filetypes=[("Excel/CSV files", "*.xlsx *.xls *.csv"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            mapping = self._controller.detect_column_mapping(file_path)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
            self._file_label.configure(text=f"Failed to read file: {exc}")
            return

        if self._controller.is_column_mapping_complete(mapping):
            self._run_analysis(file_path, mapping)
            return

        # Email (the only required field) wasn't auto-detected -- ask the
        # user to match their columns by hand before proceeding.
        headers = self._controller.get_file_headers(file_path)

        def on_mapping_confirmed(confirmed_mapping: dict[str, str]) -> None:
            self._controller.remember_column_mapping(confirmed_mapping)
            self._run_analysis(file_path, confirmed_mapping)

        ColumnMappingDialog(self, self._theme, headers, mapping, on_confirm=on_mapping_confirmed)

    def _run_analysis(self, file_path: str, mapping: dict[str, str]) -> None:
        try:
            preview = self._controller.analyze_import_file(file_path, manual_mapping=mapping)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
            self._file_label.configure(text=f"Failed to read file: {exc}")
            return

        self._preview = preview
        self._file_label.configure(text=file_path)
        self._render_preview(preview)
        self._import_button.configure(
            state="normal" if preview.valid_count else "disabled",
            text=f"Import {preview.valid_count} Valid Contact(s)",
        )

    def _render_preview(self, preview: ImportPreview) -> None:
        self._summary_labels["imported"].configure(text=str(preview.valid_count))
        self._summary_labels["skipped"].configure(text=str(preview.skipped_count))
        self._summary_labels["invalid"].configure(text=str(preview.invalid_count))
        self._summary_labels["duplicates"].configure(text=str(preview.duplicate_count))

        rows = [
            (
                str(row.row_number),
                (
                    str(row.row_number),
                    _STATUS_LABELS.get(row.status, row.status),
                    row.email,
                    row.contact_name,
                    row.company,
                    row.reason,
                ),
            )
            for row in preview.rows
        ]
        self._table.set_rows(rows)

    def _handle_commit(self) -> None:
        if self._preview is None:
            return
        summary = self._controller.commit_import(self._preview)

        self._summary_labels["imported"].configure(text=str(summary.imported))
        self._summary_labels["skipped"].configure(text=str(summary.skipped))
        self._summary_labels["invalid"].configure(text=str(summary.invalid))
        self._summary_labels["duplicates"].configure(text=str(summary.duplicates))

        self._import_button.configure(state="disabled", text="Imported")
        self._on_imported()
