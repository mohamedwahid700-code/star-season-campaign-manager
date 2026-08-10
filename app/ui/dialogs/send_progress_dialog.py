"""
Send progress dialog.

Shown while a campaign is being sent to its recipients. Polls
`BulkSendController` on a `after()` timer (never touches the
background send thread directly) to update:

    - a progress bar and "X of N" counter
    - live Sent / Failed / Remaining counts
    - the recipient currently being processed
    - Pause/Resume and Cancel controls

The dialog does not close itself when sending finishes -- the user
reviews the final summary and closes it explicitly, at which point the
caller (`CampaignsView`) refreshes the Dashboard/History-relevant state.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.controllers.bulk_send_controller import BulkSendController
from app.ui.dialogs.base_dialog import BaseDialog
from app.ui.theme.theme_manager import ThemeManager

_POLL_MS = 150


class SendProgressDialog(BaseDialog):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        bulk_send_controller: BulkSendController,
        campaign_name: str,
        total_recipients: int,
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(
            master, theme_manager, title="Sending Campaign",
            preferred_width=560, preferred_height=440,
            min_width=440, min_height=380,
        )
        self._controller = bulk_send_controller
        self._on_finished = on_finished
        self._total = total_recipients
        self._finished = False

        # A user-closable dialog with live background work should not be
        # dismissable via the window manager's own close button while
        # sending is still in progress -- Cancel is the explicit way out.
        self.protocol("WM_DELETE_WINDOW", self._handle_close_attempt)

        self.content.columnconfigure(0, weight=1)

        self._build_header(campaign_name)
        self._build_progress_area()
        self._build_counts_area()
        self._build_footer()

        self._poll()

    def _build_header(self, campaign_name: str) -> None:
        ctk.CTkLabel(
            self.content, text=campaign_name, font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self._theme.color("text_primary"), anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        self._current_recipient_label = ctk.CTkLabel(
            self.content, text="Preparing to send...", font=ctk.CTkFont(size=12),
            text_color=self._theme.color("text_secondary"), anchor="w",
        )
        self._current_recipient_label.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

    def _build_progress_area(self) -> None:
        self._progress_bar = ctk.CTkProgressBar(
            self.content, height=16, corner_radius=8,
            fg_color=self._theme.color("surface_alt"), progress_color=self._theme.color("primary"),
        )
        self._progress_bar.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 6))
        self._progress_bar.set(0)

        self._progress_text_label = ctk.CTkLabel(
            self.content, text=f"0 of {self._total}", font=ctk.CTkFont(size=12),
            text_color=self._theme.color("text_secondary"),
        )
        self._progress_text_label.grid(row=3, column=0, sticky="w", padx=16, pady=(0, 16))

    def _build_counts_area(self) -> None:
        counts_row = ctk.CTkFrame(self.content, fg_color="transparent")
        counts_row.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 16))
        for i in range(3):
            counts_row.columnconfigure(i, weight=1)

        self._sent_value_label = self._build_count_card(counts_row, 0, "Sent", self._theme.color("success"))
        self._failed_value_label = self._build_count_card(counts_row, 1, "Failed", self._theme.color("danger"))
        self._remaining_value_label = self._build_count_card(
            counts_row, 2, "Remaining", self._theme.color("text_secondary")
        )

    def _build_count_card(self, parent: ctk.CTkFrame, column: int, label: str, color: str) -> ctk.CTkLabel:
        card = ctk.CTkFrame(parent, fg_color=self._theme.color("surface"), corner_radius=8)
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 6, 0))

        value_label = ctk.CTkLabel(
            card, text="0", font=ctk.CTkFont(size=22, weight="bold"), text_color=color,
        )
        value_label.pack(pady=(10, 0))
        ctk.CTkLabel(
            card, text=label, font=ctk.CTkFont(size=11), text_color=self._theme.color("text_secondary"),
        ).pack(pady=(0, 10))
        return value_label

    def _build_footer(self) -> None:
        self.footer.columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            self.footer, text="", font=ctk.CTkFont(size=12), text_color=self._theme.color("text_secondary"),
        )
        self._status_label.grid(row=0, column=0, sticky="w", padx=16, pady=16)

        button_row = ctk.CTkFrame(self.footer, fg_color="transparent")
        button_row.grid(row=0, column=1, sticky="e", padx=16, pady=12)

        self._pause_button = ctk.CTkButton(
            button_row, text="Pause", width=90, height=34, corner_radius=8,
            fg_color=self._theme.color("surface_alt"), hover_color=self._theme.color("border"),
            text_color=self._theme.color("text_primary"), command=self._handle_pause_resume,
        )
        self._pause_button.pack(side="left", padx=(0, 8))

        self._cancel_button = ctk.CTkButton(
            button_row, text="Cancel", width=90, height=34, corner_radius=8,
            fg_color=self._theme.color("danger"), hover_color=self._theme.color("danger"),
            text_color="#FFFFFF", command=self._handle_cancel,
        )
        self._cancel_button.pack(side="left", padx=(0, 8))

        self._close_button = ctk.CTkButton(
            button_row, text="Close", width=90, height=34, corner_radius=8, state="disabled",
            fg_color=self._theme.color("primary"), hover_color=self._theme.color("primary_hover"),
            text_color=self._theme.color("text_on_primary"), command=self.destroy,
        )
        self._close_button.pack(side="left")

    # ------------------------------------------------------------------
    def _handle_pause_resume(self) -> None:
        if self._controller.is_paused():
            self._controller.resume()
            self._pause_button.configure(text="Pause")
            self._status_label.configure(text="Sending...")
        else:
            self._controller.pause()
            self._pause_button.configure(text="Resume")
            self._status_label.configure(text="Paused.")

    def _handle_cancel(self) -> None:
        self._controller.cancel()
        self._status_label.configure(text="Cancelling...")
        self._cancel_button.configure(state="disabled")
        self._pause_button.configure(state="disabled")

    def _handle_close_attempt(self) -> None:
        if self._finished:
            self.destroy()
        # While sending is in progress, ignore the window-manager close
        # button -- Cancel is the explicit, intentional way to stop.

    def _poll(self) -> None:
        for event in self._controller.poll_events():
            self._apply_event(event)

        if self._finished:
            return

        self.after(_POLL_MS, self._poll)

    def _apply_event(self, event) -> None:
        processed = event.sent_count + event.failed_count
        self._progress_bar.set(processed / self._total if self._total else 0)
        self._progress_text_label.configure(text=f"{processed} of {self._total}")
        self._sent_value_label.configure(text=str(event.sent_count))
        self._failed_value_label.configure(text=str(event.failed_count))
        self._remaining_value_label.configure(text=str(max(self._total - processed, 0)))

        if event.kind == "sending" and event.contact is not None:
            account_suffix = f" via {event.account}" if event.account else ""
            self._current_recipient_label.configure(
                text=f"Sending to {event.contact.display_name} <{event.contact.email}>{account_suffix}"
            )
        elif event.kind == "sent" and event.contact is not None:
            account_suffix = f" via {event.account}" if event.account else ""
            self._current_recipient_label.configure(
                text=f"Sent to {event.contact.display_name} <{event.contact.email}>{account_suffix}"
            )
        elif event.kind == "failed" and event.contact is not None:
            account_suffix = f" [{event.account}]" if event.account else ""
            self._current_recipient_label.configure(
                text=f"Failed: {event.contact.email}{account_suffix} -- {event.error_message}"
            )
        elif event.kind == "done":
            self._finish(f"Done. Sent {event.sent_count}, failed {event.failed_count}.")
        elif event.kind == "cancelled":
            self._finish(f"Cancelled. Sent {event.sent_count}, failed {event.failed_count} before stopping.")

    def _finish(self, message: str) -> None:
        self._finished = True
        self._current_recipient_label.configure(text=message)
        self._status_label.configure(text="Finished.")
        self._pause_button.configure(state="disabled")
        self._cancel_button.configure(state="disabled")
        self._close_button.configure(state="normal")
        if self._on_finished:
            self._on_finished()
