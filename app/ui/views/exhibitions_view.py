"""Exhibitions view.

Exhibition Management page: list + Create/Edit, plus an
exhibition-scoped Import (Excel/CSV with preview) and a participants
panel that shows every `ExhibitionContact` linked to the currently
selected Exhibition -- the same list a future campaign send would draw
its recipients from.
"""

from __future__ import annotations

import customtkinter as ctk

from app.controllers.exhibition_contact_controller import ExhibitionContactController
from app.controllers.exhibition_controller import ExhibitionController
from app.models.exhibition import Exhibition
from app.ui.components.data_table import DataTable
from app.ui.dialogs.exhibition_dialog import ExhibitionDialog
from app.ui.dialogs.exhibition_import_dialog import ExhibitionImportDialog
from app.ui.views.base_view import BaseView

_EXHIBITION_COLUMNS = [
    ("name", "Exhibition Name", 220),
    ("location", "Location", 160),
    ("start_date", "Start Date", 100),
    ("end_date", "End Date", 100),
    ("participants", "Participants", 100),
]

_PARTICIPANT_COLUMNS = [
    ("contact_name", "Contact Name", 160),
    ("company", "Company", 150),
    ("email", "Email", 200),
    ("stand_number", "Stand", 80),
    ("lead_stage_name", "Stage", 100),
    ("source", "Source", 180),
]


class ExhibitionsView(BaseView):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        exhibition_controller: ExhibitionController,
        exhibition_contact_controller: ExhibitionContactController,
    ) -> None:
        self._controller = exhibition_controller
        self._participant_controller = exhibition_contact_controller
        self._selected_exhibition: Exhibition | None = None
        super().__init__(
            master, title="Exhibitions",
            subtitle="Manage exhibitions and the participants linked to each one.",
        )

    def build_content(self) -> None:
        self.content.rowconfigure(1, weight=3)
        self.content.rowconfigure(3, weight=2)
        self._build_toolbar()
        self._build_exhibitions_table()
        self._build_participants_header()
        self._build_participants_table()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_toolbar(self) -> None:
        toolbar = ctk.CTkFrame(self.content, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        toolbar.columnconfigure(0, weight=1)

        button_group = ctk.CTkFrame(toolbar, fg_color="transparent")
        button_group.grid(row=0, column=1, sticky="e")

        self._edit_button = ctk.CTkButton(
            button_group, text="Edit", width=90, height=34, corner_radius=8, state="disabled",
            fg_color=self.theme.color("surface_alt"), hover_color=self.theme.color("border"),
            text_color=self.theme.color("text_primary"), command=self._handle_edit_selected,
        )
        self._edit_button.pack(side="left", padx=(0, 8))

        self._import_button = ctk.CTkButton(
            button_group, text="Import Participants", width=170, height=34, corner_radius=8,
            state="disabled",
            fg_color=self.theme.color("surface_alt"), hover_color=self.theme.color("border"),
            text_color=self.theme.color("text_primary"), command=self._handle_import,
        )
        self._import_button.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            button_group, text="+ New Exhibition", width=150, height=34, corner_radius=8,
            fg_color=self.theme.color("primary"), hover_color=self.theme.color("primary_hover"),
            text_color=self.theme.color("text_on_primary"),
            command=self._handle_add,
        ).pack(side="left")

    def _build_exhibitions_table(self) -> None:
        table_container = ctk.CTkFrame(
            self.content, fg_color=self.theme.color("surface"), corner_radius=12,
            border_width=1, border_color=self.theme.color("border"),
        )
        table_container.grid(row=1, column=0, sticky="nsew", pady=(0, 16))
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(0, weight=1)

        self._exhibitions_table = DataTable(
            table_container, self.theme, _EXHIBITION_COLUMNS,
            on_row_double_click=self._handle_row_double_click,
            on_selection_change=self._handle_selection_change,
        )
        self._exhibitions_table.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    def _build_participants_header(self) -> None:
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)

        self._participants_label = ctk.CTkLabel(
            header, text="Participants", font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self.theme.color("text_primary"), anchor="w",
        )
        self._participants_label.grid(row=0, column=0, sticky="w")

    def _build_participants_table(self) -> None:
        table_container = ctk.CTkFrame(
            self.content, fg_color=self.theme.color("surface"), corner_radius=12,
            border_width=1, border_color=self.theme.color("border"),
        )
        table_container.grid(row=3, column=0, sticky="nsew")
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(0, weight=1)

        self._participants_table = DataTable(table_container, self.theme, _PARTICIPANT_COLUMNS)
        self._participants_table.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        exhibitions = self._controller.list_exhibitions()
        rows = [
            (
                str(exhibition.id),
                (
                    exhibition.name,
                    exhibition.location or "",
                    exhibition.start_date.strftime("%Y-%m-%d") if exhibition.start_date else "",
                    exhibition.end_date.strftime("%Y-%m-%d") if exhibition.end_date else "",
                    str(self._participant_controller.count_for_exhibition(exhibition.id)),
                ),
            )
            for exhibition in exhibitions
        ]
        self._exhibitions_table.set_rows(rows)
        self._selected_exhibition = None
        self._edit_button.configure(state="disabled")
        self._import_button.configure(state="disabled")
        self._refresh_participants(None)

    def on_show(self) -> None:
        self.refresh()

    def _refresh_participants(self, exhibition: Exhibition | None) -> None:
        if exhibition is None:
            self._participants_label.configure(text="Participants")
            self._participants_table.set_rows([])
            return

        participants = self._participant_controller.get_participants(exhibition.id)
        self._participants_label.configure(
            text=f"Participants - {exhibition.name} ({len(participants)})"
        )
        rows = [
            (
                str(p.id),
                (p.contact_name, p.company, p.email, p.stand_number, p.lead_stage_name, p.source),
            )
            for p in participants
        ]
        self._participants_table.set_rows(rows)

    # ------------------------------------------------------------------
    def _handle_selection_change(self, iid: str | None) -> None:
        exhibition = self._controller.get_exhibition(int(iid)) if iid else None
        self._selected_exhibition = exhibition
        state = "normal" if exhibition else "disabled"
        self._edit_button.configure(state=state)
        self._import_button.configure(state=state)
        self._refresh_participants(exhibition)

    def _handle_row_double_click(self, iid: str) -> None:
        self._open_edit_dialog(int(iid))

    def _handle_add(self) -> None:
        ExhibitionDialog(self, self.theme, self._controller, on_saved=self.refresh)

    def _handle_edit_selected(self) -> None:
        if self._selected_exhibition is not None:
            self._open_edit_dialog(self._selected_exhibition.id)

    def _open_edit_dialog(self, exhibition_id: int) -> None:
        exhibition = self._controller.get_exhibition(exhibition_id)
        if exhibition is None:
            return
        ExhibitionDialog(
            self, self.theme, self._controller, on_saved=self.refresh, exhibition=exhibition,
        )

    def _handle_import(self) -> None:
        if self._selected_exhibition is None:
            return

        def on_imported() -> None:
            self.refresh()

        ExhibitionImportDialog(
            self, self.theme, self._controller, self._selected_exhibition, on_imported=on_imported,
        )
