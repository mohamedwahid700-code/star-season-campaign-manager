"""Campaigns view.

Campaign list with Create / Edit / Duplicate / Archive / Delete /
Send Campaign, backed by `CampaignController`, `OutlookController`, and
`BulkSendController` for the production bulk-sending workflow.
"""

from __future__ import annotations

import customtkinter as ctk

from app.controllers.bulk_send_controller import BulkSendController
from app.controllers.campaign_controller import CampaignController
from app.controllers.contact_controller import ContactController
from app.controllers.outlook_controller import OutlookController
from app.controllers.settings_controller import SettingsController
from app.models.campaign import CampaignStatus
from app.ui.components.confirm_dialog import ask_confirm
from app.ui.components.data_table import DataTable
from app.ui.dialogs.campaign_dialog import CampaignDialog
from app.ui.dialogs.outlook_send_test_dialog import OutlookSendTestDialog
from app.ui.dialogs.recipient_selection_dialog import RecipientSelectionDialog
from app.ui.dialogs.send_progress_dialog import SendProgressDialog
from app.ui.views.base_view import BaseView

_COLUMNS = [
    ("name", "Campaign Name", 220),
    ("event_name", "Event Name", 160),
    ("language", "Language", 90),
    ("status", "Status", 110),
    ("updated_at", "Updated", 110),
]

_STATUS_LABELS = {
    CampaignStatus.DRAFT: "Draft",
    CampaignStatus.SCHEDULED: "Scheduled",
    CampaignStatus.RUNNING: "Running",
    CampaignStatus.PAUSED: "Paused",
    CampaignStatus.COMPLETED: "Completed",
    CampaignStatus.CANCELLED: "Cancelled",
    CampaignStatus.ARCHIVED: "Archived",
}


class CampaignsView(BaseView):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        campaign_controller: CampaignController,
        contact_controller: ContactController,
        outlook_controller: OutlookController,
        settings_controller: SettingsController,
    ) -> None:
        self._controller = campaign_controller
        self._contact_controller = contact_controller
        self._outlook_controller = outlook_controller
        self._settings_controller = settings_controller
        self._selected_campaign_id: int | None = None
        self._show_archived = False
        super().__init__(master, title="Campaigns", subtitle="Create and manage your email campaigns.")

    def build_content(self) -> None:
        self.content.rowconfigure(1, weight=1)
        self._build_toolbar()
        self._build_table()
        self.refresh()

    def _build_toolbar(self) -> None:
        toolbar = ctk.CTkFrame(self.content, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        toolbar.columnconfigure(0, weight=1)

        self._archived_toggle = ctk.CTkSwitch(
            toolbar, text="Show archived", font=ctk.CTkFont(size=12),
            progress_color=self.theme.color("primary"), command=self._handle_toggle_archived,
        )
        self._archived_toggle.grid(row=0, column=0, sticky="w")

        button_group = ctk.CTkFrame(toolbar, fg_color="transparent")
        button_group.grid(row=0, column=1, sticky="e")

        self._edit_button = self._toolbar_button(button_group, "Edit", self._handle_edit_selected)
        self._duplicate_button = self._toolbar_button(button_group, "Duplicate", self._handle_duplicate_selected)
        self._archive_button = self._toolbar_button(button_group, "Archive", self._handle_archive_selected)
        self._send_test_button = self._toolbar_button(
            button_group, "Send Test Email", self._handle_send_test_selected, width=140
        )
        self._delete_button = self._toolbar_button(
            button_group, "Delete", self._handle_delete_selected, danger=True
        )

        self._send_campaign_button = ctk.CTkButton(
            button_group, text="Send Campaign", width=140, height=34, corner_radius=8, state="disabled",
            fg_color=self.theme.color("success"), hover_color=self.theme.color("success"),
            text_color="#FFFFFF", command=self._handle_send_campaign_selected,
        )
        self._send_campaign_button.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            button_group, text="+ New Campaign", width=140, height=34, corner_radius=8,
            fg_color=self.theme.color("primary"), hover_color=self.theme.color("primary_hover"),
            text_color=self.theme.color("text_on_primary"),
            command=self._handle_add,
        ).pack(side="left")

    def _toolbar_button(self, parent, text, command, danger: bool = False, width: int = 90) -> ctk.CTkButton:
        button = ctk.CTkButton(
            parent, text=text, width=width, height=34, corner_radius=8, state="disabled",
            fg_color=self.theme.color("danger") if danger else self.theme.color("surface_alt"),
            hover_color=self.theme.color("danger") if danger else self.theme.color("border"),
            text_color=self.theme.color("text_primary") if not danger else "white",
            command=command,
        )
        button.pack(side="left", padx=(0, 8))
        return button

    def _build_table(self) -> None:
        table_container = ctk.CTkFrame(
            self.content, fg_color=self.theme.color("surface"), corner_radius=12,
            border_width=1, border_color=self.theme.color("border"),
        )
        table_container.grid(row=1, column=0, sticky="nsew")
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(0, weight=1)

        self._table = DataTable(
            table_container, self.theme, _COLUMNS,
            on_row_double_click=self._handle_row_double_click,
            on_selection_change=self._handle_selection_change,
        )
        self._table.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        campaigns = self._controller.list_campaigns(include_archived=self._show_archived)
        rows = [
            (
                str(c.id),
                (
                    c.name,
                    c.event_name or "",
                    c.language,
                    _STATUS_LABELS.get(c.status, c.status.value),
                    c.updated_at.strftime("%Y-%m-%d"),
                ),
            )
            for c in campaigns
        ]
        self._table.set_rows(rows)
        self._selected_campaign_id = None
        self._set_action_buttons_state("disabled")

    def on_show(self) -> None:
        self.refresh()

    def _set_action_buttons_state(self, state: str) -> None:
        for button in (
            self._edit_button, self._duplicate_button, self._archive_button,
            self._send_test_button, self._delete_button, self._send_campaign_button,
        ):
            button.configure(state=state)

    # ------------------------------------------------------------------
    def _handle_toggle_archived(self) -> None:
        self._show_archived = bool(self._archived_toggle.get())
        self.refresh()

    def _handle_selection_change(self, iid: str | None) -> None:
        self._selected_campaign_id = int(iid) if iid else None
        self._set_action_buttons_state("normal" if iid else "disabled")
        if iid:
            campaign = self._controller.get_campaign(int(iid))
            if campaign and campaign.status == CampaignStatus.ARCHIVED:
                self._archive_button.configure(text="Restore")
                self._send_campaign_button.configure(state="disabled")
            else:
                self._archive_button.configure(text="Archive")

    def _handle_row_double_click(self, iid: str) -> None:
        self._open_edit_dialog(int(iid))

    def _handle_add(self) -> None:
        CampaignDialog(self, self.theme, self._controller, self._contact_controller, on_saved=self.refresh)

    def _handle_edit_selected(self) -> None:
        if self._selected_campaign_id is not None:
            self._open_edit_dialog(self._selected_campaign_id)

    def _open_edit_dialog(self, campaign_id: int) -> None:
        campaign = self._controller.get_campaign(campaign_id)
        if campaign is None:
            return
        CampaignDialog(
            self, self.theme, self._controller, self._contact_controller,
            on_saved=self.refresh, campaign=campaign,
        )

    def _handle_duplicate_selected(self) -> None:
        if self._selected_campaign_id is None:
            return
        self._controller.duplicate_campaign(self._selected_campaign_id)
        self.refresh()

    def _handle_send_test_selected(self) -> None:
        if self._selected_campaign_id is None:
            return
        campaign = self._controller.get_campaign(self._selected_campaign_id)
        if campaign is None:
            return
        OutlookSendTestDialog(
            self, self.theme, self._outlook_controller, self._controller,
            self._contact_controller, campaign=campaign,
        )

    def _handle_send_campaign_selected(self) -> None:
        if self._selected_campaign_id is None:
            return
        campaign = self._controller.get_campaign(self._selected_campaign_id)
        if campaign is None:
            return

        account = self._outlook_controller.get_default_account()
        if not account:
            ask_confirm(
                self, self.theme, title="No Outlook Account",
                message="Set a default Outlook account in Settings before sending a campaign.",
                on_confirm=lambda: None, confirm_text="OK", danger=False,
            )
            return

        def on_recipients_chosen(contacts) -> None:
            self._confirm_and_send(campaign, contacts, account)

        RecipientSelectionDialog(self, self.theme, self._contact_controller, on_confirm=on_recipients_chosen)

    def _confirm_and_send(self, campaign, contacts, account: str) -> None:
        recipient_count = len(contacts)

        def start_sending() -> None:
            delay_seconds = self._settings_controller.get_snapshot().default_delay_seconds
            self._controller.mark_campaign_status(campaign.id, CampaignStatus.RUNNING)

            bulk_send_controller = BulkSendController()
            bulk_send_controller.start(campaign, contacts, account, delay_seconds)

            def on_finished() -> None:
                summary = bulk_send_controller.get_summary()
                if summary is not None:
                    final_status = CampaignStatus.CANCELLED if summary.cancelled else CampaignStatus.COMPLETED
                    self._controller.mark_campaign_status(campaign.id, final_status)
                self.refresh()

            SendProgressDialog(
                self, self.theme, bulk_send_controller,
                campaign_name=campaign.name, total_recipients=recipient_count,
                on_finished=on_finished,
            )

        ask_confirm(
            self, self.theme, title="Send Campaign",
            message=(
                f"Send '{campaign.name}' to {recipient_count} recipient"
                f"{'s' if recipient_count != 1 else ''} from {account}?"
            ),
            on_confirm=start_sending, confirm_text="Send", danger=False,
        )

    def _handle_archive_selected(self) -> None:
        if self._selected_campaign_id is None:
            return
        campaign = self._controller.get_campaign(self._selected_campaign_id)
        if campaign is None:
            return
        if campaign.status == CampaignStatus.ARCHIVED:
            self._controller.restore_campaign(self._selected_campaign_id)
        else:
            self._controller.archive_campaign(self._selected_campaign_id)
        self.refresh()

    def _handle_delete_selected(self) -> None:
        if self._selected_campaign_id is None:
            return
        campaign_id = self._selected_campaign_id
        campaign = self._controller.get_campaign(campaign_id)
        if campaign is None:
            return

        def do_delete() -> None:
            self._controller.delete_campaign(campaign_id)
            self.refresh()

        ask_confirm(
            self, self.theme, title="Delete Campaign",
            message=f"Delete campaign '{campaign.name}'? This cannot be undone.",
            on_confirm=do_delete,
        )
