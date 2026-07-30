"""
Top bar component.

Displays the application identity, the signed-in Windows user, the
live Outlook connection status, a light/dark theme toggle, and a
search box. The search box is present and styled per the Sprint 1
layout requirements but is not yet wired to any search logic -- that
arrives once Contacts/Campaigns have real data to search.
"""

from __future__ import annotations

import getpass

import customtkinter as ctk

from app.controllers.outlook_controller import OutlookController
from app.controllers.settings_controller import SettingsController
from app.ui.theme.theme_manager import ThemeManager


class TopBar(ctk.CTkFrame):
    HEIGHT = 64

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        settings_controller: SettingsController,
        outlook_controller: OutlookController,
        theme_manager: ThemeManager,
        app_name: str,
        on_theme_toggle,
    ) -> None:
        self._settings_controller = settings_controller
        self._outlook_controller = outlook_controller
        self._theme = theme_manager
        self._on_theme_toggle = on_theme_toggle

        super().__init__(
            master,
            height=self.HEIGHT,
            corner_radius=0,
            fg_color=theme_manager.color("surface"),
        )
        self.grid_propagate(False)
        self.columnconfigure(1, weight=1)

        self._build_identity(app_name)
        self._build_search_box()
        self._build_right_section()

    def _build_identity(self, app_name: str) -> None:
        identity_frame = ctk.CTkFrame(self, fg_color="transparent")
        identity_frame.grid(row=0, column=0, sticky="w", padx=(24, 12))

        ctk.CTkLabel(
            identity_frame,
            text=app_name,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self._theme.color("text_primary"),
        ).pack(side="left")

    def _build_search_box(self) -> None:
        self._search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Search campaigns, contacts, templates...",
            height=36,
            corner_radius=8,
            fg_color=self._theme.color("surface_alt"),
            border_width=0,
        )
        self._search_entry.grid(row=0, column=1, sticky="ew", padx=12)

    def _build_right_section(self) -> None:
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.grid(row=0, column=2, sticky="e", padx=(12, 24))

        current_user = getpass.getuser()

        ctk.CTkLabel(
            right_frame,
            text=current_user,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self._theme.color("text_primary"),
        ).pack(side="left", padx=(0, 16))

        self._outlook_label = ctk.CTkLabel(
            right_frame,
            text="Outlook: Checking...",
            font=ctk.CTkFont(size=12),
            text_color=self._theme.color("text_secondary"),
        )
        self._outlook_label.pack(side="left", padx=(0, 16))
        self.refresh_outlook_status()

        self._theme_switch = ctk.CTkSwitch(
            right_frame,
            text="Dark Mode",
            font=ctk.CTkFont(size=12),
            command=self._handle_theme_toggle,
            progress_color=self._theme.color("primary"),
        )
        if self._theme.is_dark:
            self._theme_switch.select()
        else:
            self._theme_switch.deselect()
        self._theme_switch.pack(side="left")

    def _handle_theme_toggle(self) -> None:
        self._on_theme_toggle()

    def refresh_outlook_status(self) -> None:
        """
        Re-check the live Outlook connection state and update the
        header label.

        "Connected" means Outlook initialized successfully AND at least
        one account was detected -- not merely that a default account
        string happens to be saved in Settings, which could go stale
        (e.g. Outlook was reinstalled, or the app is running on a
        machine without Outlook at all).
        """
        accounts, error = self._outlook_controller.list_accounts()

        if accounts:
            text = f"Outlook: Connected ({len(accounts)} account{'s' if len(accounts) != 1 else ''})"
            color = self._theme.color("success")
        else:
            text = "Outlook: Not Connected"
            color = self._theme.color("text_secondary")

        self._outlook_label.configure(text=text, text_color=color)
