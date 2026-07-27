"""Reports view.

Analytics and exportable reports are out of scope for Sprint 1
(foundation only). The page is fully navigable and themed so the
routing can be verified end-to-end; reporting logic lands in a later
sprint once there is campaign data to report on.
"""

from __future__ import annotations

import customtkinter as ctk

from app.ui.components.empty_state import build_empty_state
from app.ui.views.base_view import BaseView


class ReportsView(BaseView):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, title="Reports", subtitle="Analyze campaign performance over time.")

    def build_content(self) -> None:
        self.content.rowconfigure(0, weight=1)
        empty_state = build_empty_state(
            self.content,
            self.theme,
            headline="Reporting is coming soon",
            description=(
                "Delivery rates, engagement summaries, and exportable reports "
                "will be available in an upcoming sprint."
            ),
        )
        empty_state.grid(row=0, column=0, sticky="nsew")
