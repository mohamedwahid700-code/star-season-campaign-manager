"""
Template controller.

Mediates between the Templates page (list + editor dialog) and
`TemplateService` (CRUD) / `TemplateRenderingService` (variables panel +
preview rendering) -- the same rendering service the Campaign editor
uses, so a Template previews identically to how a Campaign built from
it would.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.contact import Contact
from app.models.template import Template
from app.services.template_rendering_service import TemplateRenderingService
from app.services.template_service import TemplateService


@dataclass(frozen=True)
class TemplateFormData:
    """Plain data captured from the Create/Edit Template dialog."""

    name: str
    subject: str = ""
    html_content: str = ""


class TemplateController:
    def __init__(
        self,
        template_service: TemplateService | None = None,
        rendering_service: TemplateRenderingService | None = None,
    ) -> None:
        self._template_service = template_service or TemplateService()
        self._rendering_service = rendering_service or TemplateRenderingService()

    def list_templates(self) -> list[Template]:
        return self._template_service.list_templates()

    def get_template(self, template_id: int) -> Template | None:
        return self._template_service.get_template(template_id)

    def create_template(self, data: TemplateFormData) -> Template:
        return self._template_service.create_template(data.name, data.subject, data.html_content)

    def update_template(self, template_id: int, data: TemplateFormData) -> Template:
        return self._template_service.update_template(
            template_id, data.name, data.subject, data.html_content
        )

    def delete_template(self, template_id: int) -> bool:
        return self._template_service.delete_template(template_id)

    def available_variables(self) -> list[tuple[str, str]]:
        return self._rendering_service.available_variables()

    def render_preview_html(self, html_content: str, contact: Contact | None) -> str:
        return self._rendering_service.render(html_content, contact, campaign=None)
