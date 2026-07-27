"""Repository package.

Each repository isolates all data-access logic for one model, per the
Repository Pattern. Services (and, exceptionally, controllers) depend
on repositories -- never on SQLAlchemy sessions or queries directly.
"""

from app.repositories.blacklist_repository import BlacklistRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.log_repository import LogRepository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.template_repository import TemplateRepository

__all__ = [
    "BlacklistRepository",
    "CampaignRepository",
    "ContactRepository",
    "HistoryRepository",
    "LogRepository",
    "SettingsRepository",
    "TemplateRepository",
]
