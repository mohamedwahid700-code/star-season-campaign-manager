"""History view.

The send/delivery audit trail is out of scope for Sprint 1 (foundation
only). The page is fully navigable and themed so the routing can be
verified end-to-end; the history table and filtering land in a later
sprint once the email queue exists to populate it.
"""

from __future__ import annotations

import customtkinter as ctk

from app.ui.components.empty_state import build_empty_state
from app.ui.views.base_view import BaseView


class HistoryView(BaseView):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, title="History", subtitle="Track every email sent across your campaigns.")

    def build_content(self) -> None:
        self.content.rowconfigure(0, weight=1)
        empty_state = build_empty_state(
            self.content,
            self.theme,
            headline="Send history is coming soon",
            description=(
                "Once campaigns can be sent, every delivery attempt will be "
                "logged here with status, timestamp, and error details."
            ),
        )
        empty_state.grid(row=0, column=0, sticky="nsew")
