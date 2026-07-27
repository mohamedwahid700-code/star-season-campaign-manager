"""
Outlook Send Test dialog.

The Sprint 3 MVP workflow, all in one place:

    1. Shows the selected campaign (name/subject/event) -- already read
       by the caller (`CampaignsView`).
    2. Lets the user pick one contact from the database.
    3. Renders the campaign's subject/HTML body with that contact's
       variables replaced (reusing `CampaignController.render_preview_html`,
       already built in Sprint 2 -- no new rendering logic here).
    4. "Preview Email" opens the real Outlook compose window via
       `OutlookController`, with the selected account's signature
       preserved.
    5. "Send Test Email" sends exactly one email the same way, then logs
       the outcome (time, account, recipient, success/failure, error)
       to the `history` table via `OutlookController`.
"""

from __future__ import annotations

import customtkinter as ctk

from app.controllers.campaign_controller import CampaignController
from app.controllers.contact_controller import ContactController
from app.controllers.outlook_controller import OutlookController
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.ui.dialogs.base_dialog import BaseDialog
from app.ui.dialogs.contact_picker_dialog import ContactPickerDialog
from app.ui.theme.theme_manager import ThemeManager


class OutlookSendTestDialog(BaseDialog):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        outlook_controller: OutlookController,
        campaign_controller: CampaignController,
        contact_controller: ContactController,
        campaign: Campaign,
    ) -> None:
        super().__init__(
            master, theme_manager, title="Send Test Email via Outlook",
            preferred_width=560, preferred_height=560,
            min_width=420, min_height=360,
        )
        self._outlook_controller = outlook_controller
        self._campaign_controller = campaign_controller
        self._contact_controller = contact_controller
        self._campaign = campaign
        self._selected_contact: Contact | None = None
        self._has_sent = False

        self.content.columnconfigure(0, weight=1)

        self._build_campaign_info()
        self._build_account_info()
        self._build_contact_picker()
        self._build_status_area()
        self._build_footer()

    # ------------------------------------------------------------------
    def _build_campaign_info(self) -> None:
        card = ctk.CTkFrame(self.content, fg_color=self._theme.color("surface"), corner_radius=8)
        card.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        card.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text=self._campaign.name, font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self._theme.color("text_primary"), anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 2))

        subject = self._campaign.subject or "(no subject)"
        ctk.CTkLabel(
            card, text=f"Subject: {subject}", font=ctk.CTkFont(size=12),
            text_color=self._theme.color("text_secondary"), anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))

    def _build_account_info(self) -> None:
        card = ctk.CTkFrame(self.content, fg_color=self._theme.color("surface"), corner_radius=8)
        card.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        card.columnconfigure(0, weight=1)

        account = self._outlook_controller.get_default_account()
        account_text = account if account else "No default Outlook account configured (see Settings)."

        ctk.CTkLabel(
            card, text="Sending Account", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self._theme.color("text_primary"), anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 0))
        ctk.CTkLabel(
            card, text=account_text, font=ctk.CTkFont(size=12),
            text_color=self._theme.color("text_secondary"), anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

    def _build_contact_picker(self) -> None:
        card = ctk.CTkFrame(self.content, fg_color=self._theme.color("surface"), corner_radius=8)
        card.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=0)

        ctk.CTkLabel(
            card, text="Test Contact", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self._theme.color("text_primary"), anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 4))

        self._contact_label = ctk.CTkLabel(
            card, text="No contact selected.", font=ctk.CTkFont(size=12),
            text_color=self._theme.color("text_secondary"), anchor="w", wraplength=280,
        )
        self._contact_label.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

        ctk.CTkButton(
            card, text="Choose Contact...", width=150, height=32, corner_radius=8,
            fg_color=self._theme.color("surface_alt"), hover_color=self._theme.color("border"),
            text_color=self._theme.color("text_primary"), command=self._handle_choose_contact,
        ).grid(row=1, column=1, sticky="e", padx=16, pady=(0, 12))

    def _build_status_area(self) -> None:
        self._status_label = ctk.CTkLabel(
            self.content, text="", font=ctk.CTkFont(size=12), text_color=self._theme.color("text_secondary"),
            wraplength=480, justify="left", anchor="w",
        )
        self._status_label.grid(row=3, column=0, sticky="ew", padx=16, pady=(4, 16))

    def _build_footer(self) -> None:
        self.footer.columnconfigure(0, weight=1)

        button_row = ctk.CTkFrame(self.footer, fg_color="transparent")
        button_row.grid(row=0, column=1, sticky="e", padx=16, pady=16)

        ctk.CTkButton(
            button_row, text="Close", width=90, height=36, corner_radius=8,
            fg_color=self._theme.color("surface_alt"), hover_color=self._theme.color("border"),
            text_color=self._theme.color("text_primary"), command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        self._preview_button = ctk.CTkButton(
            button_row, text="Preview Email", width=130, height=36, corner_radius=8, state="disabled",
            fg_color=self._theme.color("surface_alt"), hover_color=self._theme.color("border"),
            text_color=self._theme.color("text_primary"), command=self._handle_preview,
        )
        self._preview_button.pack(side="left", padx=(0, 8))

        self._send_button = ctk.CTkButton(
            button_row, text="Send Test Email", width=140, height=36, corner_radius=8, state="disabled",
            fg_color=self._theme.color("primary"), hover_color=self._theme.color("primary_hover"),
            text_color=self._theme.color("text_on_primary"), command=self._handle_send,
        )
        self._send_button.pack(side="left")

    # ------------------------------------------------------------------
    def _handle_choose_contact(self) -> None:
        contacts = self._contact_controller.list_contacts()
        ContactPickerDialog(self, self._theme, contacts, on_pick=self._set_selected_contact)

    def _set_selected_contact(self, contact: Contact) -> None:
        self._selected_contact = contact
        self._contact_label.configure(text=f"{contact.display_name}  <{contact.email}>")
        account = self._outlook_controller.get_default_account()
        can_act = bool(account) and not self._has_sent
        self._preview_button.configure(state="normal" if can_act else "disabled")
        self._send_button.configure(state="normal" if can_act else "disabled")
        if not account:
            self._set_status(
                "No default Outlook account is configured. Set one in Settings first.", is_error=True
            )
        else:
            self._set_status("", is_error=False)

    def _render_current_email(self) -> tuple[str, str]:
        """Return `(subject, html_body)` with every `{Variable}` replaced."""
        subject = self._campaign_controller.render_preview_html(
            self._campaign.subject, self._selected_contact, self._campaign
        )
        html_body = self._campaign_controller.render_preview_html(
            self._campaign.html_body, self._selected_contact, self._campaign
        )
        return subject, html_body

    def _handle_preview(self) -> None:
        if self._selected_contact is None:
            return
        account = self._outlook_controller.get_default_account()
        subject, html_body = self._render_current_email()

        try:
            self._outlook_controller.preview_email(
                subject=subject, html_body=html_body,
                to_email=self._selected_contact.email, account_smtp=account,
            )
            self._set_status("Preview opened in Outlook.", is_error=False)
        except Exception as exc:  # noqa: BLE001 - every Outlook COM failure lands here, never crashes
            self._set_status(f"Could not open preview: {exc}", is_error=True)

    def _handle_send(self) -> None:
        if self._selected_contact is None or self._has_sent:
            return
        account = self._outlook_controller.get_default_account()
        subject, html_body = self._render_current_email()

        result = self._outlook_controller.send_test_email(
            campaign_id=self._campaign.id,
            contact_id=self._selected_contact.id,
            subject=subject,
            html_body=html_body,
            to_email=self._selected_contact.email,
            account_smtp=account,
        )

        # "Send ONLY one test email": once an attempt has been made
        # (success or failure), disable further sends from this dialog.
        self._has_sent = True
        self._send_button.configure(state="disabled")

        if result.success:
            self._set_status(
                f"Test email sent successfully to {result.recipient} from {result.account}.",
                is_error=False,
            )
        else:
            self._set_status(f"Send failed: {result.error_message}", is_error=True)

    def _set_status(self, message: str, is_error: bool) -> None:
        color = self._theme.color("danger") if is_error else self._theme.color("success")
        self._status_label.configure(text=message, text_color=color if message else self._theme.color("text_secondary"))
