"""Contacts view.

Full Contact Management page: searchable/sortable/filterable table,
Add/Edit/Delete, Import (Excel/CSV with preview), and Export.
"""

from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk

from app.controllers.contact_controller import ContactController
from app.ui.components.confirm_dialog import ask_confirm
from app.ui.components.data_table import DataTable
from app.ui.dialogs.contact_dialog import ContactDialog
from app.ui.dialogs.contact_import_dialog import ContactImportDialog
from app.ui.views.base_view import BaseView

_COLUMNS = [
    ("contact_name", "Contact Name", 160),
    ("company", "Company", 160),
    ("email", "Email", 210),
    ("country", "Country", 110),
    ("stand_number", "Stand", 80),
    ("phone", "Phone", 130),
    ("updated_at", "Updated", 110),
]

_ALL_COUNTRIES_LABEL = "All Countries"


class ContactsView(BaseView):
    def __init__(self, master: ctk.CTkBaseClass, contact_controller: ContactController) -> None:
        self._controller = contact_controller
        self._selected_contact_id: int | None = None
        self._search_term = ""
        self._sort_by = "updated_at"
        self._sort_descending = True
        super().__init__(master, title="Contacts", subtitle="Manage exhibition participants and prospects.")

    def build_content(self) -> None:
        self.content.rowconfigure(1, weight=1)

        self._build_toolbar()
        self._build_table()
        self.refresh()

    def _build_toolbar(self) -> None:
        toolbar = ctk.CTkFrame(self.content, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        toolbar.columnconfigure(1, weight=1)

        self._search_entry = ctk.CTkEntry(toolbar, placeholder_text="Search contacts...", height=34, width=240)
        self._search_entry.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self._search_entry.bind("<Return>", lambda _e: self._handle_search())

        self._country_menu = ctk.CTkOptionMenu(
            toolbar, values=[_ALL_COUNTRIES_LABEL], height=34, width=160, command=lambda _v: self.refresh()
        )
        self._country_menu.grid(row=0, column=1, sticky="w")

        button_group = ctk.CTkFrame(toolbar, fg_color="transparent")
        button_group.grid(row=0, column=2, sticky="e")

        self._edit_button = ctk.CTkButton(
            button_group, text="Edit", width=90, height=34, corner_radius=8, state="disabled",
            fg_color=self.theme.color("surface_alt"), hover_color=self.theme.color("border"),
            text_color=self.theme.color("text_primary"), command=self._handle_edit_selected,
        )
        self._edit_button.pack(side="left", padx=(0, 8))

        self._delete_button = ctk.CTkButton(
            button_group, text="Delete", width=90, height=34, corner_radius=8, state="disabled",
            fg_color=self.theme.color("danger"), hover_color=self.theme.color("danger"),
            command=self._handle_delete_selected,
        )
        self._delete_button.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            button_group, text="Export", width=90, height=34, corner_radius=8,
            fg_color=self.theme.color("surface_alt"), hover_color=self.theme.color("border"),
            text_color=self.theme.color("text_primary"), command=self._handle_export,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            button_group, text="Import", width=90, height=34, corner_radius=8,
            fg_color=self.theme.color("surface_alt"), hover_color=self.theme.color("border"),
            text_color=self.theme.color("text_primary"), command=self._handle_import,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            button_group, text="+ Add Contact", width=130, height=34, corner_radius=8,
            fg_color=self.theme.color("primary"), hover_color=self.theme.color("primary_hover"),
            text_color=self.theme.color("text_on_primary"),
            command=self._handle_add,
        ).pack(side="left")

    def _build_table(self) -> None:
        table_container = ctk.CTkFrame(
            self.content, fg_color=self.theme.color("surface"), corner_radius=12,
            border_width=1, border_color=self.theme.color("border"),
        )
        table_container.grid(row=1, column=0, sticky="nsew")
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(0, weight=1)

        self._table = DataTable(
            table_container, self.theme, _COLUMNS,
            on_sort=self._handle_sort,
            on_row_double_click=self._handle_row_double_click,
            on_selection_change=self._handle_selection_change,
        )
        self._table.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        countries = self._controller.get_countries()
        self._country_menu.configure(values=[_ALL_COUNTRIES_LABEL] + countries)
        if self._country_menu.get() not in ([_ALL_COUNTRIES_LABEL] + countries):
            self._country_menu.set(_ALL_COUNTRIES_LABEL)

        selected_country = self._country_menu.get()
        country_filter = "" if selected_country == _ALL_COUNTRIES_LABEL else selected_country

        contacts = self._controller.list_contacts(
            search_term=self._search_term,
            country=country_filter,
            sort_by=self._sort_by,
            sort_descending=self._sort_descending,
        )

        rows = [
            (
                str(contact.id),
                (
                    contact.contact_name or "",
                    contact.company or "",
                    contact.email,
                    contact.country or "",
                    contact.stand_number or "",
                    contact.phone or "",
                    contact.updated_at.strftime("%Y-%m-%d"),
                ),
            )
            for contact in contacts
        ]
        self._table.set_rows(rows)
        self._selected_contact_id = None
        self._edit_button.configure(state="disabled")
        self._delete_button.configure(state="disabled")

    def on_show(self) -> None:
        self.refresh()

    # ------------------------------------------------------------------
    # Toolbar handlers
    # ------------------------------------------------------------------
    def _handle_search(self) -> None:
        self._search_term = self._search_entry.get().strip()
        self.refresh()

    def _handle_sort(self, column_key: str) -> None:
        if self._sort_by == column_key:
            self._sort_descending = not self._sort_descending
        else:
            self._sort_by = column_key
            self._sort_descending = False
        self.refresh()

    def _handle_selection_change(self, iid: str | None) -> None:
        self._selected_contact_id = int(iid) if iid else None
        state = "normal" if iid else "disabled"
        self._edit_button.configure(state=state)
        self._delete_button.configure(state=state)

    def _handle_row_double_click(self, iid: str) -> None:
        self._open_edit_dialog(int(iid))

    def _handle_add(self) -> None:
        ContactDialog(self, self.theme, self._controller, on_saved=self.refresh)

    def _handle_edit_selected(self) -> None:
        if self._selected_contact_id is not None:
            self._open_edit_dialog(self._selected_contact_id)

    def _open_edit_dialog(self, contact_id: int) -> None:
        contact = self._controller.get_contact(contact_id)
        if contact is None:
            return
        ContactDialog(self, self.theme, self._controller, on_saved=self.refresh, contact=contact)

    def _handle_delete_selected(self) -> None:
        if self._selected_contact_id is None:
            return
        contact_id = self._selected_contact_id
        contact = self._controller.get_contact(contact_id)
        if contact is None:
            return

        def do_delete() -> None:
            self._controller.delete_contact(contact_id)
            self.refresh()

        ask_confirm(
            self, self.theme, title="Delete Contact",
            message=f"Delete {contact.display_name} ({contact.email})? This cannot be undone.",
            on_confirm=do_delete,
        )

    def _handle_import(self) -> None:
        ContactImportDialog(self, self.theme, self._controller, on_imported=self.refresh)

    def _handle_export(self) -> None:
        contacts = self._controller.list_contacts(
            search_term=self._search_term, sort_by=self._sort_by, sort_descending=self._sort_descending
        )
        if not contacts:
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Contacts",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx"), ("CSV File", "*.csv")],
        )
        if not file_path:
            return
        self._controller.export_contacts(contacts, file_path)
