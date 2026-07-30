"""Controller package (the "C" in this application's MVC layering).

Controllers translate UI intent (button clicks, form submissions) into
service calls, and translate service results back into plain data the
views can render. Views must never import a service or repository
directly -- only a controller.
"""

from app.controllers.bulk_send_controller import BulkSendController
from app.controllers.campaign_controller import CampaignController
from app.controllers.contact_controller import ContactController
from app.controllers.dashboard_controller import DashboardController
from app.controllers.navigation_controller import NavigationController
from app.controllers.outlook_controller import OutlookController
from app.controllers.settings_controller import SettingsController
from app.controllers.template_controller import TemplateController

__all__ = [
    "BulkSendController",
    "CampaignController",
    "ContactController",
    "DashboardController",
    "NavigationController",
    "OutlookController",
    "SettingsController",
    "TemplateController",
]
