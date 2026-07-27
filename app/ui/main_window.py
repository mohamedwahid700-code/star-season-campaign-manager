"""
Main window.

This module is the application's composition root: it constructs the
service layer, the controller layer, and every view exactly once, then
wires navigation between them. No other module is responsible for
instantiating services/controllers -- everything downstream receives
them via constructor injection, which keeps every class independently
testable.
"""

from __future__ import annotations

import logging

import customtkinter as ctk

from app import __app_name__
from app.config.constants import (
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    NavigationKey,
)
from app.controllers.campaign_controller import CampaignController
from app.controllers.contact_controller import ContactController
from app.controllers.dashboard_controller import DashboardController
from app.controllers.navigation_controller import NavigationController
from app.controllers.outlook_controller import OutlookController
from app.controllers.settings_controller import SettingsController
from app.controllers.template_controller import TemplateController
from app.services.settings_service import SettingsService
from app.ui.components.sidebar import Sidebar
from app.ui.components.statusbar import StatusBar
from app.ui.components.topbar import TopBar
from app.ui.theme.theme_manager import get_theme_manager
from app.utils.paths import get_icon_path
from app.ui.views.about_view import AboutView
from app.ui.views.base_view import BaseView
from app.ui.views.campaigns_view import CampaignsView
from app.ui.views.contacts_view import ContactsView
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.history_view import HistoryView
from app.ui.views.reports_view import ReportsView
from app.ui.views.settings_view import SettingsView
from app.ui.views.templates_view import TemplatesView

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        # ------------------------------------------------------------
        # Composition root: services -> controllers -> UI
        # ------------------------------------------------------------
        self._settings_service = SettingsService()
        self._settings_controller = SettingsController(self._settings_service)
        self._dashboard_controller = DashboardController()
        self._contact_controller = ContactController(settings_service=self._settings_service)
        self._campaign_controller = CampaignController()
        self._template_controller = TemplateController()
        self._outlook_controller = OutlookController(settings_service=self._settings_service)
        self._navigation_controller = NavigationController(initial_key=NavigationKey.DASHBOARD)

        self._theme = get_theme_manager()
        self._theme.apply_mode(self._settings_service.get_theme_mode())

        self.title(__app_name__)
        self._apply_window_icon()
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        width, height = self._settings_service.get_window_size()
        self.geometry(f"{max(width, MIN_WINDOW_WIDTH)}x{max(height, MIN_WINDOW_HEIGHT)}")
        if self._settings_service.get_window_maximized():
            self.after(10, lambda: self.state("zoomed"))

        self.configure(fg_color=self._theme.color("background"))

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_layout()
        self._register_views()
        self._navigation_controller.subscribe(self._show_view)
        self._show_view(self._navigation_controller.current_key)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Layout construction
    # ------------------------------------------------------------------
    def _apply_window_icon(self) -> None:
        """
        Set the window/taskbar icon, if the bundled icon asset exists.

        Guarded end-to-end: a missing or unreadable icon file must never
        prevent the application from starting, on any platform.
        """
        try:
            ico_path = get_icon_path("app_icon.ico")
            if ico_path.exists():
                self.iconbitmap(str(ico_path))
                return
        except Exception:  # noqa: BLE001 - .iconbitmap() is Windows/Tk-version sensitive
            logger.debug("iconbitmap() unavailable; falling back to iconphoto().", exc_info=True)

        try:
            png_path = get_icon_path("app_icon.png")
            if png_path.exists():
                from PIL import Image, ImageTk

                photo = ImageTk.PhotoImage(Image.open(png_path))
                self.iconphoto(True, photo)
                self._icon_photo_ref = photo  # keep a reference alive
        except Exception:  # noqa: BLE001 - never block startup over a missing/bad icon
            logger.debug("iconphoto() fallback also unavailable; continuing without an icon.", exc_info=True)

    def _build_layout(self) -> None:
        self._sidebar = Sidebar(
            self,
            navigation_controller=self._navigation_controller,
            theme_manager=self._theme,
            app_name=__app_name__,
        )
        self._sidebar.grid(row=0, column=0, rowspan=2, sticky="ns")

        self._topbar = TopBar(
            self,
            settings_controller=self._settings_controller,
            theme_manager=self._theme,
            app_name=__app_name__,
            on_theme_toggle=self._handle_theme_toggle,
        )
        self._topbar.grid(row=0, column=1, sticky="new")

        self._content_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self._content_container.grid(row=0, column=1, sticky="nsew", pady=(TopBar.HEIGHT, StatusBar.HEIGHT))
        self._content_container.grid_rowconfigure(0, weight=1)
        self._content_container.grid_columnconfigure(0, weight=1)

        self._status_bar = StatusBar(self, theme_manager=self._theme)
        self._status_bar.grid(row=1, column=1, sticky="sew")

    def _register_views(self) -> None:
        self._views: dict[NavigationKey, BaseView] = {
            NavigationKey.DASHBOARD: DashboardView(self._content_container, self._dashboard_controller),
            NavigationKey.CAMPAIGNS: CampaignsView(
                self._content_container, self._campaign_controller, self._contact_controller,
                self._outlook_controller,
            ),
            NavigationKey.CONTACTS: ContactsView(self._content_container, self._contact_controller),
            NavigationKey.TEMPLATES: TemplatesView(
                self._content_container, self._template_controller, self._contact_controller
            ),
            NavigationKey.HISTORY: HistoryView(self._content_container),
            NavigationKey.REPORTS: ReportsView(self._content_container),
            NavigationKey.SETTINGS: SettingsView(
                self._content_container, self._settings_controller, self._theme
            ),
            NavigationKey.ABOUT: AboutView(self._content_container),
        }
        for view in self._views.values():
            view.grid(row=0, column=0, sticky="nsew")

    # ------------------------------------------------------------------
    # Navigation / theme handling
    # ------------------------------------------------------------------
    def _show_view(self, key: NavigationKey) -> None:
        view = self._views[key]
        view.tkraise()
        view.on_show()
        self._status_bar.set_status(f"Viewing {key.value.capitalize()}")

    def _handle_theme_toggle(self) -> None:
        new_mode = self._settings_controller.toggle_theme()
        self._theme.apply_mode(new_mode)
        self._rebuild_themed_ui()
        self._status_bar.set_status(f"Theme switched to {new_mode} mode")

    def _rebuild_themed_ui(self) -> None:
        """
        Destroy and recreate every themed widget in the window.

        CustomTkinter does not automatically recolor a widget's
        manually-set `fg_color`/`text_color` when the appearance mode
        changes, and patching colors on every individual widget across
        the whole app is fragile and easy to miss a spot (exactly the
        "mixed dark/light controls" problem). Rebuilding from scratch
        against the now-current theme guarantees every widget -- sidebar,
        top bar, status bar, and whichever page is currently shown -- is
        constructed with correct colors, with no stale leftovers.
        """
        current_key = self._navigation_controller.current_key

        self._sidebar.destroy()
        self._topbar.destroy()
        self._status_bar.destroy()
        self._content_container.destroy()

        # The soon-to-be-destroyed sidebar (and this window's own
        # _show_view) are both subscribed to navigation changes; clear
        # everything and re-subscribe fresh so no stale callback bound to
        # a destroyed widget ever fires again.
        self._navigation_controller.clear_subscribers()
        self._navigation_controller.subscribe(self._show_view)

        self.configure(fg_color=self._theme.color("background"))

        self._build_layout()
        self._register_views()
        self._show_view(current_key)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def _on_close(self) -> None:
        try:
            is_maximized = self.state() == "zoomed"
            self._settings_service.set_window_maximized(is_maximized)
            if not is_maximized:
                self._settings_service.set_window_size(self.winfo_width(), self.winfo_height())
        except Exception:  # noqa: BLE001 - never block shutdown on a settings write failure
            logger.exception("Failed to persist window state on close.")
        finally:
            self.destroy()
