"""
Campaign controller.

Mediates between the Campaigns page (list + editor dialog) and:
`CampaignService` for CRUD/duplicate/archive, `TemplateService` so a
campaign can be seeded from an existing template, and
`TemplateRenderingService` so the editor's Preview button can render
`{Variable}` tokens against a chosen contact.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.campaign import Campaign, CampaignStatus
from app.models.contact import Contact
from app.services.campaign_service import CampaignService
from app.services.template_rendering_service import TemplateRenderingService
from app.services.template_service import TemplateService


@dataclass(frozen=True)
class CampaignFormData:
    """Plain data captured from the Create/Edit Campaign dialog."""

    name: str
    event_name: str = ""
    exhibition_id: int | None = None
    language: str = "English"
    subject: str = ""
    html_body: str = ""


class CampaignController:
    def __init__(
        self,
        campaign_service: CampaignService | None = None,
        template_service: TemplateService | None = None,
        rendering_service: TemplateRenderingService | None = None,
    ) -> None:
        self._campaign_service = campaign_service or CampaignService()
        self._template_service = template_service or TemplateService()
        self._rendering_service = rendering_service or TemplateRenderingService()

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------
    def list_campaigns(self, include_archived: bool = False) -> list[Campaign]:
        return self._campaign_service.list_campaigns(include_archived=include_archived)

    def get_campaign(self, campaign_id: int) -> Campaign | None:
        return self._campaign_service.get_campaign(campaign_id)

    def list_templates_for_picker(self) -> list[tuple[int, str]]:
        """Return `(id, name)` pairs for the "start from template" dropdown."""
        return [(t.id, t.name) for t in self._template_service.list_templates()]

    def get_template(self, template_id: int):
        return self._template_service.get_template(template_id)

    # ------------------------------------------------------------------
    # Create / edit / duplicate / archive / delete
    # ------------------------------------------------------------------
    def create_campaign(self, data: CampaignFormData) -> Campaign:
        return self._campaign_service.create_campaign(
            name=data.name,
            event_name=data.event_name,
            exhibition_id=data.exhibition_id,
            language=data.language,
            subject=data.subject,
            html_body=data.html_body,
        )

    def create_campaign_from_template(self, name: str, template_id: int) -> Campaign:
        return self._campaign_service.create_campaign_from_template(name, template_id)

    def update_campaign(self, campaign_id: int, data: CampaignFormData) -> Campaign:
        return self._campaign_service.update_campaign(
            campaign_id,
            name=data.name,
            event_name=data.event_name,
            exhibition_id=data.exhibition_id,
            language=data.language,
            subject=data.subject,
            html_body=data.html_body,
        )

    def duplicate_campaign(self, campaign_id: int) -> Campaign:
        return self._campaign_service.duplicate_campaign(campaign_id)

    def archive_campaign(self, campaign_id: int) -> Campaign:
        return self._campaign_service.archive_campaign(campaign_id)

    def restore_campaign(self, campaign_id: int) -> Campaign:
        return self._campaign_service.restore_campaign(campaign_id)

    def mark_campaign_status(self, campaign_id: int, status: CampaignStatus) -> Campaign:
        return self._campaign_service.mark_status(campaign_id, status)

    def delete_campaign(self, campaign_id: int) -> bool:
        return self._campaign_service.delete_campaign(campaign_id)

    # ------------------------------------------------------------------
    # Variables / preview
    # ------------------------------------------------------------------
    def available_variables(self) -> list[tuple[str, str]]:
        return self._rendering_service.available_variables()

    def render_preview_html(
        self, html_body: str, contact: Contact | None, campaign: Campaign | None = None
    ) -> str:
        return self._rendering_service.render(html_body, contact, campaign)
