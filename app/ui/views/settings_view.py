"""Settings view.

The one page in Sprint 1 with real, working business logic: reading
and writing user preferences through `SettingsController`. Everything
else on this page (campaign defaults, Outlook account, etc.) is plain
configuration, not campaign/email business logic, so it is in scope
for the foundation sprint.
"""

from __future__ import annotations

import customtkinter as ctk

from app.controllers.settings_controller import SettingsController
from app.ui.theme.theme_manager import ThemeManager
from app.ui.views.base_view import BaseView


class SettingsView(BaseView):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        settings_controller: SettingsController,
        theme_manager: ThemeManager,
    ) -> None:
        self._controller = settings_controller
        self._theme_manager = theme_manager

        self._company_entry: ctk.CTkEntry | None = None
        self._language_menu: ctk.CTkOptionMenu | None = None
        self._theme_menu: ctk.CTkOptionMenu | None = None
        self._delay_entry: ctk.CTkEntry | None = None
        self._outlook_menu: ctk.CTkOptionMenu | None = None
        self._outlook_entry: ctk.CTkEntry | None = None
        self._outlook_status_label: ctk.CTkLabel | None = None
        self._outlook_field_container: ctk.CTkFrame | None = None
        self._outlook_accounts_by_label: dict[str, str] = {}
        self._status_label: ctk.CTkLabel | None = None

        super().__init__(master, title="Settings", subtitle="Configure company defaults and preferences.")

    def build_content(self) -> None:
        snapshot = self._controller.get_snapshot()

        card = ctk.CTkFrame(
            self.content,
            fg_color=self.theme.color("surface"),
            corner_radius=12,
            border_width=1,
            border_color=self.theme.color("border"),
        )
        card.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(1, weight=1)
        self.content.rowconfigure(0, weight=0)

        row = 0
        row = self._add_field(card, row, "Company Name")
        self._company_entry = ctk.CTkEntry(card, height=36)
        self._company_entry.insert(0, snapshot.company_name)
        self._company_entry.grid(row=row - 1, column=1, sticky="ew", padx=(0, 24), pady=12)

        row = self._add_field(card, row, "Default Language")
        self._language_menu = ctk.CTkOptionMenu(card, values=snapshot.supported_languages, height=36)
        self._language_menu.set(snapshot.default_language)
        self._language_menu.grid(row=row - 1, column=1, sticky="w", padx=(0, 24), pady=12)

        row = self._add_field(card, row, "Theme")
        self._theme_menu = ctk.CTkOptionMenu(card, values=snapshot.supported_themes, height=36)
        self._theme_menu.set(snapshot.theme_mode)
        self._theme_menu.grid(row=row - 1, column=1, sticky="w", padx=(0, 24), pady=12)

        row = self._add_field(card, row, "Default Delay (seconds)")
        self._delay_entry = ctk.CTkEntry(card, height=36)
        self._delay_entry.insert(0, str(snapshot.default_delay_seconds))
        self._delay_entry.grid(row=row - 1, column=1, sticky="w", padx=(0, 24), pady=12)

        row = self._add_field(card, row, "Default Outlook Account")
        self._outlook_field_container = ctk.CTkFrame(card, fg_color="transparent")
        self._outlook_field_container.grid(row=row - 1, column=1, sticky="ew", padx=(0, 24), pady=12)
        self._outlook_field_container.columnconfigure(0, weight=1)
        self._build_outlook_account_field(snapshot.default_outlook_account)

        button_row = ctk.CTkFrame(card, fg_color="transparent")
        button_row.grid(row=row, column=0, columnspan=2, sticky="ew", padx=24, pady=(12, 24))
        button_row.columnconfigure(1, weight=1)

        save_button = ctk.CTkButton(
            button_row,
            text="Save Settings",
            height=38,
            corner_radius=8,
            fg_color=self.theme.color("primary"),
            hover_color=self.theme.color("primary_hover"),
            text_color=self.theme.color("text_on_primary"),
            command=self._on_save_clicked,
        )
        save_button.grid(row=0, column=0, sticky="w")

        self._status_label = ctk.CTkLabel(button_row, text="", text_color=self.theme.color("success"))
        self._status_label.grid(row=0, column=1, sticky="e")

    def _build_outlook_account_field(self, current_value: str) -> None:
        for widget in self._outlook_field_container.winfo_children():
            widget.destroy()
        self._outlook_menu = None
        self._outlook_entry = None
        self._outlook_accounts_by_label = {}

        accounts, error_message = self._controller.list_outlook_accounts()

        row_frame = ctk.CTkFrame(self._outlook_field_container, fg_color="transparent")
        row_frame.grid(row=0, column=0, sticky="ew")
        row_frame.columnconfigure(0, weight=1)

        if accounts:
            labels = [f"{a.display_name} <{a.smtp_address}>" for a in accounts]
            self._outlook_accounts_by_label = {
                label: account.smtp_address for label, account in zip(labels, accounts)
            }
            self._outlook_menu = ctk.CTkOptionMenu(row_frame, values=labels, height=36)
            current_label = next(
                (label for label, smtp in self._outlook_accounts_by_label.items() if smtp == current_value),
                labels[0],
            )
            self._outlook_menu.set(current_label)
            self._outlook_menu.grid(row=0, column=0, sticky="ew")
        else:
            # Outlook not detected (wrong platform, not installed, or not
            # running): fall back to manual entry so the app stays usable.
            self._outlook_entry = ctk.CTkEntry(row_frame, height=36, placeholder_text="name@company.com")
            self._outlook_entry.insert(0, current_value)
            self._outlook_entry.grid(row=0, column=0, sticky="ew")

        ctk.CTkButton(
            row_frame, text="Refresh", width=80, height=36, corner_radius=8,
            fg_color=self.theme.color("surface_alt"), hover_color=self.theme.color("border"),
            text_color=self.theme.color("text_primary"),
            command=lambda: self._build_outlook_account_field(self._get_selected_outlook_account()),
        ).grid(row=0, column=1, padx=(8, 0))

        if error_message:
            status_text = error_message
        elif accounts:
            status_text = f"{len(accounts)} account(s) detected."
        else:
            status_text = ""

        self._outlook_status_label = ctk.CTkLabel(
            self._outlook_field_container,
            text=status_text,
            font=ctk.CTkFont(size=11),
            text_color=self.theme.color("text_secondary"),
            anchor="w",
        )
        self._outlook_status_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

    def _get_selected_outlook_account(self) -> str:
        if self._outlook_menu is not None:
            return self._outlook_accounts_by_label.get(self._outlook_menu.get(), "")
        if self._outlook_entry is not None:
            return self._outlook_entry.get().strip()
        return ""

    def _add_field(self, card: ctk.CTkFrame, row: int, label_text: str) -> int:
        ctk.CTkLabel(
            card,
            text=label_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.theme.color("text_primary"),
            anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=24, pady=12)
        return row + 1

    def _on_save_clicked(self) -> None:
        delay_text = (self._delay_entry.get() if self._delay_entry else "0").strip()
        try:
            delay_seconds = int(delay_text) if delay_text else 0
        except ValueError:
            self._set_status("Delay must be a whole number of seconds.", is_error=True)
            return

        self._controller.save_general_settings(
            company_name=self._company_entry.get() if self._company_entry else "",
            default_language=self._language_menu.get() if self._language_menu else "English",
            default_delay_seconds=delay_seconds,
            default_outlook_account=self._get_selected_outlook_account(),
        )

        new_theme = self._theme_menu.get() if self._theme_menu else self._theme_manager.mode
        if new_theme != self._theme_manager.mode:
            self._controller.set_theme_mode(new_theme)
            self._theme_manager.apply_mode(new_theme)

        self._set_status("Settings saved successfully.", is_error=False)

    def _set_status(self, message: str, is_error: bool) -> None:
        if self._status_label is None:
            return
        color = self.theme.color("danger") if is_error else self.theme.color("success")
        self._status_label.configure(text=message, text_color=color)
