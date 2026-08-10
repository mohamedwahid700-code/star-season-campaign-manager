"""
Campaign service.

CRUD orchestration for `Campaign`, plus the two operations that are
more than a plain field update: duplicating a campaign (copy everything
except identity/timestamps, always landing back in Draft) and archiving
one (a soft, reversible status change rather than a delete).

Sending-related behavior (Outlook, queueing, delays) is explicitly out
of scope for this sprint and is not present here.
"""

from __future__ import annotations

import logging

from app.models.campaign import Campaign, CampaignStatus
from app.models.template import Template
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.template_repository import TemplateRepository

logger = logging.getLogger(__name__)


class CampaignService:
    def __init__(
        self,
        repository: CampaignRepository | None = None,
        template_repository: TemplateRepository | None = None,
    ) -> None:
        self._repository = repository or CampaignRepository()
        self._template_repository = template_repository or TemplateRepository()

    def list_campaigns(self, include_archived: bool = False) -> list[Campaign]:
        campaigns = list(self._repository.get_all())
        if not include_archived:
            campaigns = [c for c in campaigns if c.status != CampaignStatus.ARCHIVED]
        campaigns.sort(key=lambda c: c.updated_at, reverse=True)
        return campaigns

    def get_campaign(self, campaign_id: int) -> Campaign | None:
        return self._repository.get_by_id(campaign_id)

    def create_campaign(
        self,
        name: str,
        event_name: str = "",
        language: str = "English",
        subject: str = "",
        html_body: str = "",
        template_id: int | None = None,
        exhibition_id: int | None = None,
    ) -> Campaign:
        campaign = Campaign(
            name=name.strip(),
            event_name=event_name.strip() or None,
            exhibition_id=exhibition_id,
            language=language,
            subject=subject,
            html_body=html_body,
            template_id=template_id,
            status=CampaignStatus.DRAFT,
        )
        created = self._repository.add(campaign)
        logger.info("Campaign created: id=%s name=%s", created.id, created.name)
        return created

    def create_campaign_from_template(self, name: str, template_id: int) -> Campaign:
        """Seed a new campaign's subject/HTML body from an existing Template."""
        template: Template | None = self._template_repository.get_by_id(template_id)
        if template is None:
            raise ValueError(f"Template with id={template_id} does not exist.")

        return self.create_campaign(
            name=name,
            subject=template.subject,
            html_body=template.html_content,
            template_id=template.id,
        )

    def update_campaign(
        self,
        campaign_id: int,
        name: str,
        event_name: str = "",
        language: str = "English",
        subject: str = "",
        html_body: str = "",
        exhibition_id: int | None = None,
    ) -> Campaign:
        campaign = self._repository.get_by_id(campaign_id)
        if campaign is None:
            raise ValueError(f"Campaign with id={campaign_id} does not exist.")

        campaign.name = name.strip()
        campaign.event_name = event_name.strip() or None
        campaign.exhibition_id = exhibition_id
        campaign.language = language
        campaign.subject = subject
        campaign.html_body = html_body

        updated = self._repository.update(campaign)
        logger.info("Campaign updated: id=%s name=%s", updated.id, updated.name)
        return updated

    def duplicate_campaign(self, campaign_id: int) -> Campaign:
        """Create a new Draft campaign that is a copy of an existing one."""
        source = self._repository.get_by_id(campaign_id)
        if source is None:
            raise ValueError(f"Campaign with id={campaign_id} does not exist.")

        duplicate = Campaign(
            name=f"{source.name} (Copy)",
            description=source.description,
            event_name=source.event_name,
            exhibition_id=source.exhibition_id,
            language=source.language,
            subject=source.subject,
            html_body=source.html_body,
            template_id=source.template_id,
            status=CampaignStatus.DRAFT,
        )
        created = self._repository.add(duplicate)
        logger.info("Campaign duplicated: source_id=%s new_id=%s", campaign_id, created.id)
        return created

    def archive_campaign(self, campaign_id: int) -> Campaign:
        campaign = self._repository.get_by_id(campaign_id)
        if campaign is None:
            raise ValueError(f"Campaign with id={campaign_id} does not exist.")
        campaign.status = CampaignStatus.ARCHIVED
        updated = self._repository.update(campaign)
        logger.info("Campaign archived: id=%s", campaign_id)
        return updated

    def restore_campaign(self, campaign_id: int) -> Campaign:
        """Move an archived campaign back to Draft."""
        campaign = self._repository.get_by_id(campaign_id)
        if campaign is None:
            raise ValueError(f"Campaign with id={campaign_id} does not exist.")
        campaign.status = CampaignStatus.DRAFT
        updated = self._repository.update(campaign)
        logger.info("Campaign restored from archive: id=%s", campaign_id)
        return updated

    def mark_status(self, campaign_id: int, status: CampaignStatus) -> Campaign:
        """Set a campaign's status directly, e.g. RUNNING/COMPLETED around a bulk send."""
        campaign = self._repository.get_by_id(campaign_id)
        if campaign is None:
            raise ValueError(f"Campaign with id={campaign_id} does not exist.")
        campaign.status = status
        updated = self._repository.update(campaign)
        logger.info("Campaign status changed: id=%s status=%s", campaign_id, status.value)
        return updated

    def delete_campaign(self, campaign_id: int) -> bool:
        deleted = self._repository.delete(campaign_id)
        if deleted:
            logger.info("Campaign deleted: id=%s", campaign_id)
        return deleted
