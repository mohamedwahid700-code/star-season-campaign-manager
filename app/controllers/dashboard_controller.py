"""
Dashboard controller.

Aggregates read-only counts from multiple repositories into a single
snapshot for the Dashboard view. Kept as a controller (not a service)
because it performs no business logic of its own -- it only composes
existing repository reads for display purposes.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.repositories.campaign_repository import CampaignRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.template_repository import TemplateRepository


@dataclass(frozen=True)
class DashboardSnapshot:
    total_campaigns: int
    total_contacts: int
    total_templates: int
    total_emails_sent: int


class DashboardController:
    def __init__(
        self,
        campaign_repository: CampaignRepository | None = None,
        contact_repository: ContactRepository | None = None,
        template_repository: TemplateRepository | None = None,
        history_repository: HistoryRepository | None = None,
    ) -> None:
        self._campaign_repository = campaign_repository or CampaignRepository()
        self._contact_repository = contact_repository or ContactRepository()
        self._template_repository = template_repository or TemplateRepository()
        self._history_repository = history_repository or HistoryRepository()

    def get_snapshot(self) -> DashboardSnapshot:
        return DashboardSnapshot(
            total_campaigns=self._campaign_repository.count(),
            total_contacts=self._contact_repository.count(),
            total_templates=self._template_repository.count(),
            total_emails_sent=self._history_repository.count(),
        )
