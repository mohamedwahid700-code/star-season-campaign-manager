"""Exhibition create/edit dialog - a simple field form for one exhibition."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

import customtkinter as ctk

from app.controllers.exhibition_controller import ExhibitionController, ExhibitionFormData
from app.models.exhibition import Exhibition
from app.ui.dialogs.base_dialog import BaseDialog
from app.ui.theme.theme_manager import ThemeManager

_DATE_FORMAT = "%Y-%m-%d"


def _parse_date(text: str) -> datetime | None:
    text = text.strip()
    if not text:
        return None
    return datetime.strptime(text, _DATE_FORMAT)


class ExhibitionDialog(BaseDialog):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        exhibition_controller: ExhibitionController,
        on_saved: Callable[[], None],
        exhibition: Exhibition | None = None,
    ) -> None:
        super().__init__(
            master, theme_manager,
            title="Edit Exhibition" if exhibition else "Add Exhibition",
            preferred_width=480, preferred_height=560,
            min_width=380, min_height=320,
        )
        self._controller = exhibition_controller
        self._on_saved = on_saved
        self._exhibition = exhibition

        self.content.columnconfigure(0, weight=1)

        fields = [
            ("Exhibition Name *", "name"),
            ("Location", "location"),
            ("Start Date (YYYY-MM-DD)", "start_date"),
            ("End Date (YYYY-MM-DD)", "end_date"),
        ]

        self._entries: dict[str, ctk.CTkEntry] = {}
        row = 0
        for label_text, field_name in fields:
            ctk.CTkLabel(
                self.content, text=label_text, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=theme_manager.color("text_primary"), anchor="w",
            ).grid(row=row, column=0, sticky="w", padx=20, pady=(14 if row == 0 else 8, 2))
            row += 1
            entry = ctk.CTkEntry(self.content, height=34)
            entry.grid(row=row, column=0, sticky="ew", padx=20)
            self._entries[field_name] = entry
            row += 1

        ctk.CTkLabel(
            self.content, text="Notes", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=theme_manager.color("text_primary"), anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=20, pady=(8, 2))
        row += 1
        self._notes_box = ctk.CTkTextbox(self.content, height=90)
        self._notes_box.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 20))
        row += 1

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

        ctk.CTkButton(
            button_row, text="Save Exhibition", width=140, height=36, corner_radius=8,
            fg_color=theme_manager.color("primary"), hover_color=theme_manager.color("primary_hover"),
            text_color=theme_manager.color("text_on_primary"), command=self._handle_save,
        ).pack(side="left")

        if exhibition:
            self._entries["name"].insert(0, exhibition.name)
            self._entries["location"].insert(0, exhibition.location or "")
            if exhibition.start_date:
                self._entries["start_date"].insert(0, exhibition.start_date.strftime(_DATE_FORMAT))
            if exhibition.end_date:
                self._entries["end_date"].insert(0, exhibition.end_date.strftime(_DATE_FORMAT))
            self._notes_box.insert("1.0", exhibition.notes or "")

    def _handle_save(self) -> None:
        try:
            start_date = _parse_date(self._entries["start_date"].get())
            end_date = _parse_date(self._entries["end_date"].get())
        except ValueError:
            self._status_label.configure(text="Dates must be in YYYY-MM-DD format.")
            return

        data = ExhibitionFormData(
            name=self._entries["name"].get().strip(),
            location=self._entries["location"].get().strip(),
            start_date=start_date,
            end_date=end_date,
            notes=self._notes_box.get("1.0", "end-1c").strip(),
        )

        try:
            if self._exhibition:
                self._controller.update_exhibition(self._exhibition.id, data)
            else:
                self._controller.create_exhibition(data)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
            self._status_label.configure(text=str(exc))
            return

        self._on_saved()
        self.destroy()
