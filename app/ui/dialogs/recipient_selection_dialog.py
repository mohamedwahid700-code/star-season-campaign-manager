"""
Recipient selection dialog.

First step of the Send Campaign workflow: choose whether to send to
every contact on file, or to a specific hand-picked subset. Uses the
same `DataTable` component as the Contacts page, in multi-select mode,
so picking recipients out of a large imported list (hundreds of
exhibitor contacts) works the same way users already know from that
page.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.controllers.contact_controller import ContactController
from app.models.contact import Contact
from app.ui.components.data_table import DataTable
from app.ui.dialogs.base_dialog import activate_grab, apply_screen_aware_geometry
from app.ui.theme.theme_manager import ThemeManager

_COLUMNS = [
    ("contact_name", "Contact Name", 160),
    ("company", "Company", 160),
    ("email", "Email", 210),
    ("country", "Country", 120),
]


class RecipientSelectionDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        contact_controller: ContactController,
        on_confirm: Callable[[list[Contact]], None],
    ) -> None:
        super().__init__(master, fg_color=theme_manager.color("background"))
        self._theme = theme_manager
        self._contact_controller = contact_controller
        self._on_confirm = on_confirm
        self._contacts_by_id: dict[str, Contact] = {}

        self.title("Select Recipients")
        self.transient(master)
        apply_screen_aware_geometry(
            self, preferred_width=760, preferred_height=620, min_width=560, min_height=420
        )

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._all_contacts = contact_controller.list_contacts()

        self._build_mode_row()
        self._build_table()
        self._build_footer()
        self._handle_mode_change()

        self.after(50, self._activate_grab)

    def _activate_grab(self) -> None:
        activate_grab(self)

    # ------------------------------------------------------------------
    def _build_mode_row(self) -> None:
        card = ctk.CTkFrame(self, fg_color=self._theme.color("surface"), corner_radius=8)
        card.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        self._mode_var = ctk.StringVar(value="all")

        ctk.CTkRadioButton(
            card, text=f"All Contacts ({len(self._all_contacts)})", variable=self._mode_var,
            value="all", text_color=self._theme.color("text_primary"),
            fg_color=self._theme.color("primary"), command=self._handle_mode_change,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=12)

        ctk.CTkRadioButton(
            card, text="Select Contacts", variable=self._mode_var,
            value="select", text_color=self._theme.color("text_primary"),
            fg_color=self._theme.color("primary"), command=self._handle_mode_change,
        ).grid(row=0, column=1, sticky="w", padx=16, pady=12)

    def _build_table(self) -> None:
        self._table_container = ctk.CTkFrame(
            self, fg_color=self._theme.color("surface"), corner_radius=8,
        )
        self._table_container.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=16, pady=(0, 8))
        self._table_container.columnconfigure(0, weight=1)
        self._table_container.rowconfigure(1, weight=1)

        self._selection_toolbar = ctk.CTkFrame(self._table_container, fg_color="transparent")
        self._selection_toolbar.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))

        ctk.CTkButton(
            self._selection_toolbar, text="Select All", width=90, height=28, corner_radius=6,
            fg_color=self._theme.color("surface_alt"), hover_color=self._theme.color("border"),
            text_color=self._theme.color("text_primary"), command=self._handle_select_all,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            self._selection_toolbar, text="Clear", width=90, height=28, corner_radius=6,
            fg_color=self._theme.color("surface_alt"), hover_color=self._theme.color("border"),
            text_color=self._theme.color("text_primary"), command=self._handle_clear_selection,
        ).pack(side="left")

        self._selected_count_label = ctk.CTkLabel(
            self._selection_toolbar, text="", font=ctk.CTkFont(size=12),
            text_color=self._theme.color("text_secondary"),
        )
        self._selected_count_label.pack(side="right")

        self._table = DataTable(
            self._table_container, self._theme, _COLUMNS,
            selectmode="extended", on_selection_change=self._handle_selection_change,
        )
        self._table.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        rows = []
        for contact in self._all_contacts:
            iid = str(contact.id)
            self._contacts_by_id[iid] = contact
            rows.append((
                iid,
                (contact.contact_name or "", contact.company or "", contact.email, contact.country or ""),
            ))
        self._table.set_rows(rows)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 16))
        footer.columnconfigure(0, weight=1)

        button_row = ctk.CTkFrame(footer, fg_color="transparent")
        button_row.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            button_row, text="Cancel", width=100, height=36, corner_radius=8,
            fg_color=self._theme.color("surface_alt"), hover_color=self._theme.color("border"),
            text_color=self._theme.color("text_primary"), command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        self._continue_button = ctk.CTkButton(
            button_row, text="Continue", width=110, height=36, corner_radius=8,
            fg_color=self._theme.color("primary"), hover_color=self._theme.color("primary_hover"),
            text_color=self._theme.color("text_on_primary"), command=self._handle_continue,
        )
        self._continue_button.pack(side="left")

    # ------------------------------------------------------------------
    def _handle_mode_change(self) -> None:
        is_select_mode = self._mode_var.get() == "select"
        state = "normal" if is_select_mode else "disabled"
        for child in self._selection_toolbar.winfo_children():
            if isinstance(child, ctk.CTkButton):
                child.configure(state=state)

        if is_select_mode:
            self._update_selected_count()
        else:
            self._selected_count_label.configure(text="")
        self._update_continue_state()

    def _handle_select_all(self) -> None:
        self._table.select_all()
        self._update_selected_count()

    def _handle_clear_selection(self) -> None:
        self._table.clear_selection()
        self._update_selected_count()

    def _handle_selection_change(self, _iid: str | None) -> None:
        self._update_selected_count()

    def _update_selected_count(self) -> None:
        if self._mode_var.get() == "select":
            count = len(self._table.get_selected_iids())
            self._selected_count_label.configure(text=f"{count} of {len(self._all_contacts)} selected")
        self._update_continue_state()

    def _update_continue_state(self) -> None:
        if self._mode_var.get() == "all":
            can_continue = len(self._all_contacts) > 0
        else:
            can_continue = len(self._table.get_selected_iids()) > 0
        self._continue_button.configure(state="normal" if can_continue else "disabled")

    def _handle_continue(self) -> None:
        if self._mode_var.get() == "all":
            selected_contacts = list(self._all_contacts)
        else:
            iids = self._table.get_selected_iids()
            selected_contacts = [self._contacts_by_id[iid] for iid in iids]

        if not selected_contacts:
            return

        self.destroy()
        self._on_confirm(selected_contacts)
