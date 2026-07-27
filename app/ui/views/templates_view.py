"""Templates view.

Reusable HTML Template library: list + Create / Edit / Delete, backed
by `TemplateController`. Uses the same `HtmlEditor` + variables panel +
Preview workflow as the Campaign editor.
"""

from __future__ import annotations

import customtkinter as ctk

from app.controllers.contact_controller import ContactController
from app.controllers.template_controller import TemplateController
from app.ui.components.confirm_dialog import ask_confirm
from app.ui.components.data_table import DataTable
from app.ui.dialogs.template_dialog import TemplateDialog
from app.ui.views.base_view import BaseView

_COLUMNS = [
    ("name", "Template Name", 220),
    ("subject", "Subject", 280),
    ("updated_at", "Updated", 110),
]


class TemplatesView(BaseView):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        template_controller: TemplateController,
        contact_controller: ContactController,
    ) -> None:
        self._controller = template_controller
        self._contact_controller = contact_controller
        self._selected_template_id: int | None = None
        super().__init__(master, title="Templates", subtitle="Design reusable HTML email templates.")

    def build_content(self) -> None:
        self.content.rowconfigure(1, weight=1)
        self._build_toolbar()
        self._build_table()
        self.refresh()

    def _build_toolbar(self) -> None:
        toolbar = ctk.CTkFrame(self.content, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        toolbar.columnconfigure(0, weight=1)

        button_group = ctk.CTkFrame(toolbar, fg_color="transparent")
        button_group.grid(row=0, column=1, sticky="e")

        self._edit_button = ctk.CTkButton(
            button_group, text="Edit", width=90, height=34, corner_radius=8, state="disabled",
            fg_color=self.theme.color("surface_alt"), hover_color=self.theme.color("border"),
            text_color=self.theme.color("text_primary"), command=self._handle_edit_selected,
        )
        self._edit_button.pack(side="left", padx=(0, 8))

        self._delete_button = ctk.CTkButton(
            button_group, text="Delete", width=90, height=34, corner_radius=8, state="disabled",
            fg_color=self.theme.color("danger"), hover_color=self.theme.color("danger"),
            command=self._handle_delete_selected,
        )
        self._delete_button.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            button_group, text="+ New Template", width=140, height=34, corner_radius=8,
            fg_color=self.theme.color("primary"), hover_color=self.theme.color("primary_hover"),
            text_color=self.theme.color("text_on_primary"),
            command=self._handle_add,
        ).pack(side="left")

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
        templates = self._controller.list_templates()
        rows = [
            (
                str(t.id),
                (t.name, t.subject, t.updated_at.strftime("%Y-%m-%d")),
            )
            for t in templates
        ]
        self._table.set_rows(rows)
        self._selected_template_id = None
        self._edit_button.configure(state="disabled")
        self._delete_button.configure(state="disabled")

    def on_show(self) -> None:
        self.refresh()

    # ------------------------------------------------------------------
    def _handle_selection_change(self, iid: str | None) -> None:
        self._selected_template_id = int(iid) if iid else None
        state = "normal" if iid else "disabled"
        self._edit_button.configure(state=state)
        self._delete_button.configure(state=state)

    def _handle_row_double_click(self, iid: str) -> None:
        self._open_edit_dialog(int(iid))

    def _handle_add(self) -> None:
        TemplateDialog(self, self.theme, self._controller, self._contact_controller, on_saved=self.refresh)

    def _handle_edit_selected(self) -> None:
        if self._selected_template_id is not None:
            self._open_edit_dialog(self._selected_template_id)

    def _open_edit_dialog(self, template_id: int) -> None:
        template = self._controller.get_template(template_id)
        if template is None:
            return
        TemplateDialog(
            self, self.theme, self._controller, self._contact_controller,
            on_saved=self.refresh, template=template,
        )

    def _handle_delete_selected(self) -> None:
        if self._selected_template_id is None:
            return
        template_id = self._selected_template_id
        template = self._controller.get_template(template_id)
        if template is None:
            return

        def do_delete() -> None:
            self._controller.delete_template(template_id)
            self.refresh()

        ask_confirm(
            self, self.theme, title="Delete Template",
            message=f"Delete template '{template.name}'? This cannot be undone.",
            on_confirm=do_delete,
        )
