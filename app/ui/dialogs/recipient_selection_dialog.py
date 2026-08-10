"""
Recipient selection dialog.

First step of the Send Campaign workflow: choose whether to send to
every recipient, or to a specific hand-picked subset. Uses the same
`DataTable` component as the Contacts page, in multi-select mode, so
picking recipients out of a large list works the same way users
already know from that page.

Exhibition-aware (Production Bulk Email Engine): when the campaign is
associated with a real Exhibition, recipients are loaded through
`ExhibitionContact` -- only contacts linked to that Exhibition are
eligible, exactly like the Exhibition participant list shown on the
Exhibitions page. This never falls back to the entire global Contact
database, and it never duplicates a global Contact record -- the
`Contact` behind each participant row is the same one already stored,
just resolved via its `contact_id` so mail-merge (`{Website}`,
`{WhatsApp}`, ...) still has every field to work with.

Legacy campaigns with no `exhibition_id` (created before this
feature) keep the original "every Contact on file" behavior
unchanged, so nothing that already worked breaks.

Either way, recipients with no usable email address are dropped
before the table is even populated -- they can never be selected or
counted, so a campaign can never be started with an invalid
recipient. `on_confirm` is still called with plain `Contact` objects,
exactly as before, so the bulk-send pipeline downstream needs no
changes.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.controllers.contact_controller import ContactController
from app.controllers.exhibition_contact_controller import ExhibitionContactController
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.ui.components.data_table import DataTable
from app.ui.dialogs.base_dialog import activate_grab, apply_screen_aware_geometry
from app.ui.theme.theme_manager import ThemeManager

_CONTACT_COLUMNS = [
    ("contact_name", "Contact Name", 160),
    ("company", "Company", 160),
    ("email", "Email", 210),
    ("country", "Country", 120),
]

_EXHIBITION_COLUMNS = [
    ("contact_name", "Contact Name", 150),
    ("company", "Company", 150),
    ("email", "Email", 200),
    ("stand_number", "Stand #", 90),
    ("lead_stage_name", "Stage", 110),
]


def _is_valid_email(email: str | None) -> bool:
    if not email:
        return False
    email = email.strip()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        return False
    return "." in email.split("@")[-1]


class RecipientSelectionDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        contact_controller: ContactController,
        on_confirm: Callable[[list[Contact]], None],
        campaign: Campaign | None = None,
        exhibition_contact_controller: ExhibitionContactController | None = None,
    ) -> None:
        super().__init__(master, fg_color=theme_manager.color("background"))
        self._theme = theme_manager
        self._contact_controller = contact_controller
        self._exhibition_contact_controller = exhibition_contact_controller or ExhibitionContactController()
        self._on_confirm = on_confirm
        self._campaign = campaign

        self._is_exhibition_scoped = bool(campaign is not None and campaign.exhibition_id is not None)

        # iid (str(contact_id)) -> (display_row_values, Contact). Built once,
        # up front, so the table only ever shows recipients that are both
        # eligible (linked to the Exhibition, or global if legacy) and have
        # a usable email address.
        self._rows_by_id: dict[str, tuple[tuple, Contact]] = {}
        self._total_eligible_before_filter = 0
        self._build_recipient_index()

        self.title("Select Recipients")
        self.transient(master)
        apply_screen_aware_geometry(
            self, preferred_width=760, preferred_height=640, min_width=560, min_height=440
        )

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_mode_row()
        self._build_table()
        self._build_footer()
        self._handle_mode_change()

        self.after(50, self._activate_grab)

    def _activate_grab(self) -> None:
        activate_grab(self)

    # ------------------------------------------------------------------
    def _build_recipient_index(self) -> None:
        if self._is_exhibition_scoped:
            participants = self._exhibition_contact_controller.get_participants(self._campaign.exhibition_id)
            self._total_eligible_before_filter = len(participants)
            for participant in participants:
                if not _is_valid_email(participant.email):
                    continue
                contact = self._contact_controller.get_contact(participant.contact_id)
                if contact is None:
                    # Linked Contact was deleted after the ExhibitionContact
                    # row was created -- skip rather than send to nothing.
                    continue
                iid = str(contact.id)
                values = (
                    participant.contact_name, participant.company, participant.email,
                    participant.stand_number, participant.lead_stage_name,
                )
                self._rows_by_id[iid] = (values, contact)
        else:
            contacts = self._contact_controller.list_contacts()
            self._total_eligible_before_filter = len(contacts)
            for contact in contacts:
                if not _is_valid_email(contact.email):
                    continue
                iid = str(contact.id)
                values = (contact.contact_name or "", contact.company or "", contact.email, contact.country or "")
                self._rows_by_id[iid] = (values, contact)

    @property
    def _skipped_invalid_count(self) -> int:
        return max(self._total_eligible_before_filter - len(self._rows_by_id), 0)

    # ------------------------------------------------------------------
    def _build_mode_row(self) -> None:
        card = ctk.CTkFrame(self, fg_color=self._theme.color("surface"), corner_radius=8)
        card.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 4))

        self._mode_var = ctk.StringVar(value="all")

        total = len(self._rows_by_id)
        all_label = (
            f"All Exhibition Participants ({total})" if self._is_exhibition_scoped else f"All Contacts ({total})"
        )
        select_label = "Select Participants" if self._is_exhibition_scoped else "Select Contacts"

        ctk.CTkRadioButton(
            card, text=all_label, variable=self._mode_var,
            value="all", text_color=self._theme.color("text_primary"),
            fg_color=self._theme.color("primary"), command=self._handle_mode_change,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=12)

        ctk.CTkRadioButton(
            card, text=select_label, variable=self._mode_var,
            value="select", text_color=self._theme.color("text_primary"),
            fg_color=self._theme.color("primary"), command=self._handle_mode_change,
        ).grid(row=0, column=1, sticky="w", padx=16, pady=12)

        if self._skipped_invalid_count:
            ctk.CTkLabel(
                self, text=(
                    f"{self._skipped_invalid_count} record"
                    f"{'s' if self._skipped_invalid_count != 1 else ''} skipped (missing/invalid email)."
                ),
                font=ctk.CTkFont(size=11), text_color=self._theme.color("text_secondary"),
            ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 4))

    def _build_table(self) -> None:
        self._table_container = ctk.CTkFrame(
            self, fg_color=self._theme.color("surface"), corner_radius=8,
        )
        self._table_container.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 8))
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

        columns = _EXHIBITION_COLUMNS if self._is_exhibition_scoped else _CONTACT_COLUMNS
        self._table = DataTable(
            self._table_container, self._theme, columns,
            selectmode="extended", on_selection_change=self._handle_selection_change,
        )
        self._table.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        rows = [(iid, values) for iid, (values, _contact) in self._rows_by_id.items()]
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
            self._selected_count_label.configure(text=f"{count} of {len(self._rows_by_id)} selected")
        self._update_continue_state()

    def _update_continue_state(self) -> None:
        if self._mode_var.get() == "all":
            can_continue = len(self._rows_by_id) > 0
        else:
            can_continue = len(self._table.get_selected_iids()) > 0
        self._continue_button.configure(state="normal" if can_continue else "disabled")

    def _handle_continue(self) -> None:
        if self._mode_var.get() == "all":
            selected_ids = list(self._rows_by_id.keys())
        else:
            selected_ids = self._table.get_selected_iids()

        selected_contacts = [self._rows_by_id[iid][1] for iid in selected_ids if iid in self._rows_by_id]

        if not selected_contacts:
            return

        self.destroy()
        self._on_confirm(selected_contacts)
