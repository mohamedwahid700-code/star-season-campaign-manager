"""
Column mapping dialog.

Shown only when the automatic header-alias detection in
`ContactImportExportService` couldn't find a required column (in
practice: email). Lets the user manually assign which column in their
file corresponds to each Contact field. The resulting mapping is
handed back to the caller, which is responsible for persisting it via
`SettingsService.set_contact_import_column_mapping()` so the same file
layout is recognized automatically next time.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.ui.dialogs.base_dialog import BaseDialog
from app.ui.theme.theme_manager import ThemeManager

_NONE_OPTION = "(Not mapped)"

# (canonical field, display label, required)
_FIELD_DEFINITIONS: list[tuple[str, str, bool]] = [
    ("email", "Email *", True),
    ("contact_name", "Contact Name", False),
    ("company", "Company Name", False),
    ("country", "Country", False),
    ("website", "Website", False),
    ("phone", "Phone", False),
    ("stand_number", "Stand Number", False),
    ("notes", "Notes", False),
]


class ColumnMappingDialog(BaseDialog):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        headers: list[str],
        initial_mapping: dict[str, str],
        on_confirm: Callable[[dict[str, str]], None],
    ) -> None:
        """
        Parameters
        ----------
        headers:
            Raw column headers found in the file being imported.
        initial_mapping:
            Best-guess `raw_header -> canonical_field` mapping to
            pre-select from (auto-detected aliases merged with any
            previously-remembered manual mapping).
        on_confirm:
            Called with the final `raw_header -> canonical_field`
            mapping once the user confirms (email is guaranteed to be
            mapped to something at that point).
        """
        super().__init__(
            master, theme_manager, title="Match Your Columns",
            preferred_width=480, preferred_height=680,
            min_width=380, min_height=320,
        )
        self._headers = headers
        self._on_confirm = on_confirm
        self._field_menus: dict[str, ctk.CTkOptionMenu] = {}

        # Invert the initial mapping (canonical -> raw header) so each
        # field's dropdown can be pre-selected.
        canonical_to_header = {canonical: header for header, canonical in initial_mapping.items()}

        self.content.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.content,
            text="We couldn't automatically find a required column.\nPlease match your file's columns below.",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=theme_manager.color("text_primary"),
            justify="left",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 12))

        options = [_NONE_OPTION] + list(headers)

        row = 1
        for canonical_field, label_text, required in _FIELD_DEFINITIONS:
            ctk.CTkLabel(
                self.content, text=label_text, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=theme_manager.color("text_primary"), anchor="w",
            ).grid(row=row, column=0, sticky="w", padx=20, pady=(10, 2))
            row += 1

            menu = ctk.CTkOptionMenu(self.content, values=options, height=32)
            preselected = canonical_to_header.get(canonical_field)
            menu.set(preselected if preselected in options else _NONE_OPTION)
            if required:
                menu.configure(command=lambda _v: self._refresh_confirm_state())
            menu.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 4))
            self._field_menus[canonical_field] = menu
            row += 1

        # Bottom padding inside the scroll area so the last field isn't
        # flush against the footer's top edge.
        ctk.CTkFrame(self.content, fg_color="transparent", height=8).grid(row=row, column=0)

        self._status_label = ctk.CTkLabel(
            self.footer, text="", font=ctk.CTkFont(size=12), text_color=theme_manager.color("danger"),
        )
        self._status_label.grid(row=0, column=0, sticky="w", padx=20, pady=16)

        button_row = ctk.CTkFrame(self.footer, fg_color="transparent")
        button_row.grid(row=0, column=1, sticky="e", padx=20, pady=12)

        ctk.CTkButton(
            button_row, text="Cancel", width=100, height=36, corner_radius=8,
            fg_color=theme_manager.color("surface_alt"), hover_color=theme_manager.color("border"),
            text_color=theme_manager.color("text_primary"), command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        self._confirm_button = ctk.CTkButton(
            button_row, text="Continue", width=110, height=36, corner_radius=8,
            fg_color=theme_manager.color("primary"), hover_color=theme_manager.color("primary_hover"),
            text_color=theme_manager.color("text_on_primary"), command=self._handle_confirm,
        )
        self._confirm_button.pack(side="left")

    def _refresh_confirm_state(self) -> None:
        if self._field_menus["email"].get() == _NONE_OPTION:
            self._status_label.configure(text="Email must be mapped to continue.")
        else:
            self._status_label.configure(text="")

    def _handle_confirm(self) -> None:
        if self._field_menus["email"].get() == _NONE_OPTION:
            self._status_label.configure(text="Email must be mapped to continue.")
            return

        final_mapping: dict[str, str] = {}
        for canonical_field, menu in self._field_menus.items():
            selected_header = menu.get()
            if selected_header != _NONE_OPTION:
                final_mapping[selected_header] = canonical_field

        self.destroy()
        self._on_confirm(final_mapping)
