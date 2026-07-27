"""View package (the "V" in this application's MVC layering).

Every page is a `BaseView` subclass rendered inside the main window's
content area. Views read data only through controllers; they never
import a service or repository directly.
"""

from app.ui.views.about_view import AboutView
from app.ui.views.base_view import BaseView
from app.ui.views.campaigns_view import CampaignsView
from app.ui.views.contacts_view import ContactsView
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.history_view import HistoryView
from app.ui.views.reports_view import ReportsView
from app.ui.views.settings_view import SettingsView
from app.ui.views.templates_view import TemplatesView

__all__ = [
    "AboutView",
    "BaseView",
    "CampaignsView",
    "ContactsView",
    "DashboardView",
    "HistoryView",
    "ReportsView",
    "SettingsView",
    "TemplatesView",
]
