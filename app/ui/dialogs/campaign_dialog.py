"""
Campaign create/edit dialog.

Same editing surface as `TemplateDialog` (HTML editor + variables panel
+ preview), plus the campaign-specific fields (event name, language)
and, only when creating a new campaign, an optional "start from
template" picker that seeds the subject/HTML body from an existing
Template.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.config.constants import CAMPAIGN_LANGUAGES
from app.controllers.campaign_controller import CampaignController, CampaignFormData
from app.controllers.contact_controller import ContactController
from app.models.campaign import Campaign
from app.ui.components.html_editor import HtmlEditor
from app.ui.components.variables_panel import build_variables_panel
from app.ui.dialogs.base_dialog import activate_grab, apply_screen_aware_geometry
from app.ui.dialogs.contact_picker_dialog import ContactPickerDialog
from app.ui.theme.theme_manager import ThemeManager
from app.utils.html_preview import open_html_preview


class CampaignDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        campaign_controller: CampaignController,
        contact_controller: ContactController,
        on_saved: Callable[[], None],
        campaign: Campaign | None = None,
    ) -> None:
        super().__init__(master, fg_color=theme_manager.color("background"))
        self._theme = theme_manager
        self._controller = campaign_controller
        self._contact_controller = contact_controller
        self._on_saved = on_saved
        self._campaign = campaign

        self.title("Edit Campaign" if campaign else "New Campaign")
        self.transient(master)
        apply_screen_aware_geometry(
            self, preferred_width=1150, preferred_height=760, min_width=760, min_height=480
        )

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_header_fields()
        self._build_editor_area()
        self._build_footer()

        if campaign:
            self._name_entry.insert(0, campaign.name)
            self._event_entry.insert(0, campaign.event_name or "")
            self._language_menu.set(campaign.language)
            self._subject_entry.insert(0, campaign.subject)
            self.editor.load_html(campaign.html_body)
        else:
            self._maybe_offer_template_picker()

        self.after(50, self._activate_grab)

    def _activate_grab(self) -> None:
        activate_grab(self)

    def _build_header_fields(self) -> None:
        header = ctk.CTkFrame(self, fg_color=self._theme.color("surface"), corner_radius=8)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        for column in (1, 3):
            header.columnconfigure(column, weight=1)
        self._header = header

        def add_label(text: str, row: int, column: int) -> None:
            ctk.CTkLabel(
                header, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self._theme.color("text_primary"),
            ).grid(row=row, column=column, sticky="w", padx=(16 if column == 0 else 0, 8), pady=10)

        add_label("Campaign Name", 0, 0)
        self._name_entry = ctk.CTkEntry(header, height=34)
        self._name_entry.grid(row=0, column=1, sticky="ew", padx=(0, 16), pady=10)

        add_label("Event Name", 0, 2)
        self._event_entry = ctk.CTkEntry(header, height=34)
        self._event_entry.grid(row=0, column=3, sticky="ew", padx=(0, 16), pady=10)

        add_label("Language", 1, 0)
        self._language_menu = ctk.CTkOptionMenu(header, values=CAMPAIGN_LANGUAGES, height=34)
        self._language_menu.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=(0, 10))

        add_label("Subject", 1, 2)
        self._subject_entry = ctk.CTkEntry(header, height=34)
        self._subject_entry.grid(row=1, column=3, sticky="ew", padx=(0, 16), pady=(0, 10))

    def _build_editor_area(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=0)
        body.rowconfigure(0, weight=1)

        self.editor = HtmlEditor(body, self._theme)
        self.editor.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        variables_panel = build_variables_panel(
            body, self._theme, self._controller.available_variables(), self._insert_variable
        )
        variables_panel.grid(row=0, column=1, sticky="ns")

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 16))
        footer.columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            footer, text="", font=ctk.CTkFont(size=12), text_color=self._theme.color("danger")
        )
        self._status_label.grid(row=0, column=0, sticky="w")

        button_row = ctk.CTkFrame(footer, fg_color="transparent")
        button_row.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            button_row, text="Preview", width=100, height=36, corner_radius=8,
            fg_color=self._theme.color("surface_alt"), hover_color=self._theme.color("border"),
            text_color=self._theme.color("text_primary"), command=self._handle_preview,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            button_row, text="Cancel", width=90, height=36, corner_radius=8,
            fg_color=self._theme.color("surface_alt"), hover_color=self._theme.color("border"),
            text_color=self._theme.color("text_primary"), command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            button_row, text="Save Campaign", width=130, height=36, corner_radius=8,
            fg_color=self._theme.color("primary"), hover_color=self._theme.color("primary_hover"),
            text_color=self._theme.color("text_on_primary"),
            command=self._handle_save,
        ).pack(side="left")

    def _maybe_offer_template_picker(self) -> None:
        templates = self._controller.list_templates_for_picker()
        if not templates:
            return

        picker_row = ctk.CTkFrame(self._header, fg_color=self._theme.color("surface_alt"), corner_radius=6)
        picker_row.grid(row=2, column=0, columnspan=4, sticky="ew", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            picker_row, text="Start from a template:",
            font=ctk.CTkFont(size=12), text_color=self._theme.color("text_primary"),
        ).pack(side="left", padx=(12, 8), pady=8)

        names = [name for _id, name in templates]
        template_menu = ctk.CTkOptionMenu(picker_row, values=names, height=28)
        template_menu.pack(side="left", padx=(0, 8), pady=8)

        def apply_template() -> None:
            selected_name = template_menu.get()
            template_id = next((tid for tid, name in templates if name == selected_name), None)
            if template_id is None:
                return
            template = self._controller.get_template(template_id)
            if template is None:
                return
            self._subject_entry.delete(0, "end")
            self._subject_entry.insert(0, template.subject)
            self.editor.load_html(template.html_content)

        ctk.CTkButton(
            picker_row, text="Apply", width=70, height=28, corner_radius=6,
            fg_color=self._theme.color("primary"), hover_color=self._theme.color("primary_hover"),
            text_color=self._theme.color("text_on_primary"),
            command=apply_template,
        ).pack(side="left", padx=(0, 12), pady=8)

    def _insert_variable(self, token: str) -> None:
        self.editor.insert_variable_token(token)

    def _handle_preview(self) -> None:
        contacts = self._contact_controller.list_contacts()

        def render_with(contact) -> None:
            html = self._controller.render_preview_html(self.editor.to_html(), contact, self._campaign)
            open_html_preview(html, subject=self._subject_entry.get())

        ContactPickerDialog(self, self._theme, contacts, on_pick=render_with)

    def _handle_save(self) -> None:
        name = self._name_entry.get().strip()
        if not name:
            self._status_label.configure(text="Campaign name is required.")
            return

        data = CampaignFormData(
            name=name,
            event_name=self._event_entry.get().strip(),
            language=self._language_menu.get(),
            subject=self._subject_entry.get().strip(),
            html_body=self.editor.to_html(),
        )

        try:
            if self._campaign:
                self._controller.update_campaign(self._campaign.id, data)
            else:
                self._controller.create_campaign(data)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
            self._status_label.configure(text=str(exc))
            return

        self._on_saved()
        self.destroy()
