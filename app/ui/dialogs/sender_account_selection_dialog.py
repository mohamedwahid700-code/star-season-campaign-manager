"""
Sender account selection dialog.

Second step of the Send Campaign workflow (after recipients are
chosen): pick one or more configured Outlook sender accounts to send
from. Selecting more than one distributes recipients round-robin
across the selected accounts (see `BulkSendService.send_campaign`).

Accounts are read live from Outlook via `OutlookController.list_accounts()`
-- never invented. If live detection isn't available (non-Windows dev
machine, Outlook not running/configured) but a default account is
already configured in Settings, that single account is offered as the
only selectable option, which preserves the exact single-account
behavior the application already had before this dialog existed.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.controllers.outlook_controller import OutlookController
from app.ui.dialogs.base_dialog import activate_grab, apply_screen_aware_geometry
from app.ui.theme.theme_manager import ThemeManager


class SenderAccountSelectionDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        outlook_controller: OutlookController,
        on_confirm: Callable[[list[str]], None],
    ) -> None:
        super().__init__(master, fg_color=theme_manager.color("background"))
        self._theme = theme_manager
        self._outlook_controller = outlook_controller
        self._on_confirm = on_confirm
        self._checkbox_vars: dict[str, ctk.BooleanVar] = {}

        accounts, error_message = outlook_controller.list_accounts()
        self._account_smtps = [a.smtp_address for a in accounts]
        self._account_labels = {
            a.smtp_address: (f"{a.display_name} <{a.smtp_address}>" if a.display_name else a.smtp_address)
            for a in accounts
        }

        self._fallback_account = ""
        if not self._account_smtps:
            # Live detection unavailable -- fall back to the single
            # configured default account, exactly like the pre-existing
            # single-account Send Campaign flow.
            default_account = outlook_controller.get_default_account()
            if default_account:
                self._fallback_account = default_account
                self._account_smtps = [default_account]
                self._account_labels = {default_account: default_account}

        self._error_message = error_message if not self._fallback_account else None

        self.title("Select Sender Accounts")
        self.transient(master)
        apply_screen_aware_geometry(
            self, preferred_width=520, preferred_height=460, min_width=400, min_height=320
        )

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_header()
        self._build_account_list()
        self._build_footer()

        self.after(50, self._activate_grab)

    def _activate_grab(self) -> None:
        activate_grab(self)

    # ------------------------------------------------------------------
    def _build_header(self) -> None:
        ctk.CTkLabel(
            self, text="Select one or more sender accounts.",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self._theme.color("text_primary"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 4))

        subtitle = (
            "Selecting more than one distributes recipients round-robin across accounts."
            if self._account_smtps
            else "No Outlook accounts are available."
        )
        ctk.CTkLabel(
            self, text=subtitle, font=ctk.CTkFont(size=12),
            text_color=self._theme.color("text_secondary"), anchor="w", wraplength=460, justify="left",
        ).grid(row=0, column=0, sticky="sw", padx=20, pady=(48, 0))

    def _build_account_list(self) -> None:
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=16, pady=(12, 8))
        container.columnconfigure(0, weight=1)

        if self._error_message:
            ctk.CTkLabel(
                container, text=self._error_message, font=ctk.CTkFont(size=12),
                text_color=self._theme.color("danger"), wraplength=440, justify="left",
            ).grid(row=0, column=0, sticky="w", pady=(4, 0))
            return

        if not self._account_smtps:
            ctk.CTkLabel(
                container,
                text="No sender account is configured. Set a default Outlook account in Settings.",
                font=ctk.CTkFont(size=12), text_color=self._theme.color("text_secondary"),
                wraplength=440, justify="left",
            ).grid(row=0, column=0, sticky="w", pady=(4, 0))
            return

        for row, smtp in enumerate(self._account_smtps):
            var = ctk.BooleanVar(value=(row == 0))
            self._checkbox_vars[smtp] = var
            ctk.CTkCheckBox(
                container, text=self._account_labels[smtp], variable=var,
                text_color=self._theme.color("text_primary"), fg_color=self._theme.color("primary"),
                command=self._update_continue_state,
            ).grid(row=row, column=0, sticky="w", pady=6)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
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
            state="normal" if self._checkbox_vars else "disabled",
        )
        self._continue_button.pack(side="left")

    def _update_continue_state(self) -> None:
        any_selected = any(var.get() for var in self._checkbox_vars.values())
        self._continue_button.configure(state="normal" if any_selected else "disabled")

    def _handle_continue(self) -> None:
        selected = [smtp for smtp, var in self._checkbox_vars.items() if var.get()]
        if not selected:
            return
        self.destroy()
        self._on_confirm(selected)
