"""
Template service.

CRUD orchestration for the reusable Template library (`app/models/template.py`).
Distinct from a Campaign's own `subject`/`html_body`: a Template is a
reusable starting point that a Campaign can be created from, but once
copied onto a Campaign, editing the Template afterwards does not change
campaigns that already used it.
"""

from __future__ import annotations

import logging

from app.models.template import Template
from app.repositories.template_repository import TemplateRepository

logger = logging.getLogger(__name__)


class TemplateService:
    def __init__(self, repository: TemplateRepository | None = None) -> None:
        self._repository = repository or TemplateRepository()

    def list_templates(self) -> list[Template]:
        templates = list(self._repository.get_all())
        templates.sort(key=lambda t: t.updated_at, reverse=True)
        return templates

    def get_template(self, template_id: int) -> Template | None:
        return self._repository.get_by_id(template_id)

    def create_template(self, name: str, subject: str, html_content: str = "") -> Template:
        template = Template(name=name.strip(), subject=subject.strip(), html_content=html_content)
        created = self._repository.add(template)
        logger.info("Template created: id=%s name=%s", created.id, created.name)
        return created

    def update_template(self, template_id: int, name: str, subject: str, html_content: str) -> Template:
        template = self._repository.get_by_id(template_id)
        if template is None:
            raise ValueError(f"Template with id={template_id} does not exist.")

        template.name = name.strip()
        template.subject = subject.strip()
        template.html_content = html_content

        updated = self._repository.update(template)
        logger.info("Template updated: id=%s name=%s", updated.id, updated.name)
        return updated

    def delete_template(self, template_id: int) -> bool:
        deleted = self._repository.delete(template_id)
        if deleted:
            logger.info("Template deleted: id=%s", template_id)
        return deleted
