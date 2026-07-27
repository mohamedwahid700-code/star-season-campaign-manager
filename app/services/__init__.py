"""Service layer package.

Services orchestrate one or more repositories to fulfil an application
use case and hold whatever business logic exists at a given sprint.
UI code depends on controllers, controllers depend on services,
services depend on repositories -- never the reverse.
"""

from app.services.campaign_service import CampaignService
from app.services.contact_import_export_service import ContactImportExportService
from app.services.contact_service import ContactService
from app.services.logging_service import LoggingService
from app.services.outlook_service import OutlookService
from app.services.settings_service import SettingsService
from app.services.template_rendering_service import TemplateRenderingService
from app.services.template_service import TemplateService

__all__ = [
    "CampaignService",
    "ContactImportExportService",
    "ContactService",
    "LoggingService",
    "OutlookService",
    "SettingsService",
    "TemplateRenderingService",
    "TemplateService",
]
