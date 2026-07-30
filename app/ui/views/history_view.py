"""History view.

Every campaign delivery attempt (from a single Test Email or a full
bulk Send Campaign), with company, contact, campaign, status,
timestamp, and error details -- populated automatically by
`BulkSendService`/`OutlookService` as sends happen.
"""

from __future__ import annotations

import customtkinter as ctk

from app.controllers.history_controller import HistoryController
from app.models.history import DeliveryStatus
from app.ui.components.data_table import DataTable
from app.ui.components.empty_state import build_empty_state
from app.ui.views.base_view import BaseView

_COLUMNS = [
    ("company", "Company", 160),
    ("contact_name", "Contact Name", 150),
    ("email", "Email", 200),
    ("campaign_name", "Campaign", 160),
    ("status", "Status", 90),
    ("timestamp", "Timestamp", 140),
    ("error", "Error", 200),
]

_STATUS_LABELS = {
    DeliveryStatus.SENT: "Sent",
    DeliveryStatus.FAILED: "Failed",
    DeliveryStatus.PENDING: "Pending",
    DeliveryStatus.SKIPPED: "Skipped",
}


class HistoryView(BaseView):
    def __init__(self, master: ctk.CTkBaseClass, history_controller: HistoryController) -> None:
        self._controller = history_controller
        self._has_data = False
        super().__init__(master, title="History", subtitle="Track every email sent across your campaigns.")

    def build_content(self) -> None:
        self.content.rowconfigure(0, weight=1)
        self.refresh()

    def refresh(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()

        records = self._controller.list_history()
        self._has_data = bool(records)

        if not self._has_data:
            empty_state = build_empty_state(
                self.content, self.theme,
                headline="No send history yet",
                description=(
                    "Once a campaign is sent (as a test or a full send), every "
                    "delivery attempt will be logged here with status, timestamp, "
                    "and error details."
                ),
            )
            empty_state.grid(row=0, column=0, sticky="nsew")
            return

        table_container = ctk.CTkFrame(
            self.content, fg_color=self.theme.color("surface"), corner_radius=12,
            border_width=1, border_color=self.theme.color("border"),
        )
        table_container.grid(row=0, column=0, sticky="nsew")
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(0, weight=1)

        table = DataTable(table_container, self.theme, _COLUMNS)
        table.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        rows = []
        for record in records:
            timestamp = record.sent_at or record.created_at
            rows.append((
                str(record.id),
                (
                    record.company,
                    record.contact_name,
                    record.email,
                    record.campaign_name,
                    _STATUS_LABELS.get(record.status, record.status.value),
                    timestamp.strftime("%Y-%m-%d %H:%M"),
                    record.error_message,
                ),
            ))
        table.set_rows(rows)

    def on_show(self) -> None:
        self.refresh()
