"""Dashboard view.

Shows a small set of KPI cards summarizing the current database state,
sourced from `DashboardController`. Sprint 1 has no campaign logic, so
every count is simply the number of rows in the corresponding table
today (zero, on a fresh install) -- but the wiring through the
controller/repository layers is real and will keep working unchanged
as later sprints start populating these tables.
"""

from __future__ import annotations

import customtkinter as ctk

from app.controllers.dashboard_controller import DashboardController
from app.ui.views.base_view import BaseView


class DashboardView(BaseView):
    def __init__(self, master: ctk.CTkBaseClass, dashboard_controller: DashboardController) -> None:
        self._controller = dashboard_controller
        super().__init__(master, title="Dashboard", subtitle="An overview of your campaign activity.")

    def build_content(self) -> None:
        self.content.columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")
        self.content.rowconfigure(1, weight=1)

        snapshot = self._controller.get_snapshot()

        kpi_definitions = [
            ("Total Campaigns", snapshot.total_campaigns, self.theme.color("primary")),
            ("Total Contacts", snapshot.total_contacts, self.theme.color("info")),
            ("Templates", snapshot.total_templates, self.theme.color("success")),
            ("Emails Sent", snapshot.total_emails_sent, self.theme.color("warning")),
        ]

        for index, (label, value, accent) in enumerate(kpi_definitions):
            card = self._build_kpi_card(label, value, accent)
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 12, 0))

        placeholder = ctk.CTkFrame(
            self.content,
            fg_color=self.theme.color("surface"),
            corner_radius=12,
            border_width=1,
            border_color=self.theme.color("border"),
        )
        placeholder.grid(row=1, column=0, columnspan=4, sticky="nsew", pady=(20, 0))
        placeholder.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            placeholder,
            text="Recent campaign activity will appear here.",
            font=ctk.CTkFont(size=14),
            text_color=self.theme.color("text_secondary"),
        ).grid(row=0, column=0, pady=60)

    def _build_kpi_card(self, label: str, value: int, accent: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self.content,
            fg_color=self.theme.color("surface"),
            corner_radius=12,
            border_width=1,
            border_color=self.theme.color("border"),
        )
        card.columnconfigure(0, weight=1)

        accent_bar = ctk.CTkFrame(card, fg_color=accent, height=4, corner_radius=2)
        accent_bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 0))

        ctk.CTkLabel(
            card,
            text=str(value),
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.theme.color("text_primary"),
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(12, 0))

        ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=13),
            text_color=self.theme.color("text_secondary"),
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(2, 16))

        return card

    def on_show(self) -> None:
        """Refresh KPI counts every time the Dashboard becomes visible."""
        for widget in self.content.winfo_children():
            widget.destroy()
        self.build_content()
