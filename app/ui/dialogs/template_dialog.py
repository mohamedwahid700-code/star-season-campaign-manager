"""
Template create/edit dialog.

Combines the `HtmlEditor`, the variables side panel, and a Preview
button (which opens the rendered HTML in the system browser against a
chosen contact) into a single modal used by the Templates page for
both "New Template" and "Edit Template".
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.controllers.contact_controller import ContactController
from app.controllers.template_controller import TemplateController, TemplateFormData
from app.models.template import Template
from app.ui.components.html_editor import HtmlEditor
from app.ui.components.variables_panel import build_variables_panel
from app.ui.dialogs.base_dialog import activate_grab, apply_screen_aware_geometry
from app.ui.dialogs.contact_picker_dialog import ContactPickerDialog
from app.ui.theme.theme_manager import ThemeManager
from app.utils.html_preview import open_html_preview


class TemplateDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme_manager: ThemeManager,
        template_controller: TemplateController,
        contact_controller: ContactController,
        on_saved: Callable[[], None],
        template: Template | None = None,
    ) -> None:
        super().__init__(master, fg_color=theme_manager.color("background"))
        self._theme = theme_manager
        self._controller = template_controller
        self._contact_controller = contact_controller
        self._on_saved = on_saved
        self._template = template

        self.title("Edit Template" if template else "New Template")
        self.transient(master)
        apply_screen_aware_geometry(
            self, preferred_width=1100, preferred_height=720, min_width=720, min_height=460
        )

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_header_fields()
        self._build_editor_area()
        self._build_footer()

        if template:
            self._name_entry.insert(0, template.name)
            self._subject_entry.insert(0, template.subject)
            self.editor.load_html(template.html_content)

        self.after(50, self._activate_grab)

    def _activate_grab(self) -> None:
        activate_grab(self)

    def _build_header_fields(self) -> None:
        header = ctk.CTkFrame(self, fg_color=self._theme.color("surface"), corner_radius=8)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header.columnconfigure(1, weight=1)
        header.columnconfigure(3, weight=1)

        ctk.CTkLabel(header, text="Template Name", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self._theme.color("text_primary")).grid(row=0, column=0, sticky="w", padx=(16, 8), pady=14)
        self._name_entry = ctk.CTkEntry(header, height=34)
        self._name_entry.grid(row=0, column=1, sticky="ew", padx=(0, 16), pady=14)

        ctk.CTkLabel(header, text="Subject", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self._theme.color("text_primary")).grid(row=0, column=2, sticky="w", padx=(0, 8), pady=14)
        self._subject_entry = ctk.CTkEntry(header, height=34)
        self._subject_entry.grid(row=0, column=3, sticky="ew", padx=(0, 16), pady=14)

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
            button_row, text="Save Template", width=130, height=36, corner_radius=8,
            fg_color=self._theme.color("primary"), hover_color=self._theme.color("primary_hover"),
            text_color=self._theme.color("text_on_primary"),
            command=self._handle_save,
        ).pack(side="left")

    def _insert_variable(self, token: str) -> None:
        self.editor.insert_variable_token(token)

    def _handle_preview(self) -> None:
        contacts = self._contact_controller.list_contacts()

        def render_with(contact) -> None:
            html = self._controller.render_preview_html(self.editor.to_html(), contact)
            open_html_preview(html, subject=self._subject_entry.get())

        ContactPickerDialog(self, self._theme, contacts, on_pick=render_with)

    def _handle_save(self) -> None:
        name = self._name_entry.get().strip()
        subject = self._subject_entry.get().strip()

        if not name:
            self._status_label.configure(text="Template name is required.")
            return

        html_content = self.editor.to_html()
        data = TemplateFormData(name=name, subject=subject, html_content=html_content)

        try:
            if self._template:
                self._controller.update_template(self._template.id, data)
            else:
                self._controller.create_template(data)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
            self._status_label.configure(text=str(exc))
            return

        self._on_saved()
        self.destroy()
