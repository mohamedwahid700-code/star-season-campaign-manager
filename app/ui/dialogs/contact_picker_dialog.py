"""
Contact picker dialog.

A small modal used by the Preview button in both the Campaign and
Template editors: the user selects any existing contact, and the
caller renders the HTML body with that contact's data substituted for
every `{Variable}` token.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.models.contact import Contact
from app.ui.dialogs.base_dialog import activate_grab, apply_screen_aware_geometry
from app.ui.theme.theme_manager import ThemeManager


class ContactPickerDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        contacts: list[Contact],
        on_pick: Callable[[Contact], None],
    ) -> None:
        super().__init__(master, fg_color=theme_manager.color("surface"))
        self._theme = theme_manager
        self._on_pick = on_pick
        self._contacts = contacts

        self.title("Preview As Contact")
        self.transient(master)
        apply_screen_aware_geometry(
            self, preferred_width=420, preferred_height=480, min_width=340, min_height=280
        )

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text="Choose a contact to preview with real data:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=theme_manager.color("text_primary"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))

        if not contacts:
            ctk.CTkLabel(
                self,
                text="No contacts yet. Add or import contacts first to preview with real data.",
                font=ctk.CTkFont(size=12),
                text_color=theme_manager.color("text_secondary"),
                wraplength=360,
                justify="left",
            ).grid(row=1, column=0, sticky="new", padx=20)
        else:
            scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
            scroll_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
            scroll_frame.columnconfigure(0, weight=1)

            for index, contact in enumerate(contacts):
                label = contact.display_name
                if contact.company and contact.company != label:
                    label = f"{label}  ·  {contact.company}"
                ctk.CTkButton(
                    scroll_frame,
                    text=f"{label}\n{contact.email}",
                    anchor="w",
                    height=48,
                    corner_radius=8,
                    fg_color=theme_manager.color("surface_alt"),
                    hover_color=theme_manager.color("border"),
                    text_color=theme_manager.color("text_primary"),
                    font=ctk.CTkFont(size=12),
                    command=lambda c=contact: self._handle_pick(c),
                ).grid(row=index, column=0, sticky="ew", pady=4)

        self.after(50, self._activate_grab)

    def _activate_grab(self) -> None:
        activate_grab(self)

    def _handle_pick(self, contact: Contact) -> None:
        self.destroy()
        self._on_pick(contact)
