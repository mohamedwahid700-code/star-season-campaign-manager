"""
Settings controller.

In this application's MVC layering:

    Model      -> app/models       (SQLAlchemy ORM entities)
    View       -> app/ui/views     (CustomTkinter frames, no data access)
    Controller -> app/controllers  (this package)

Views never talk to services or repositories directly. They call a
controller method, which talks to the service layer and returns plain
Python values the view can render. This keeps every CustomTkinter frame
free of business logic and easy to unit test by swapping controllers.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.constants import SUPPORTED_LANGUAGES, ThemeMode
from app.services.outlook_service import OutlookAccount, OutlookService, OutlookServiceError
from app.services.settings_service import SettingsService


@dataclass(frozen=True)
class SettingsSnapshot:
    """Read-only view of every user-facing setting, for populating the Settings page."""

    company_name: str
    default_language: str
    theme_mode: str
    default_delay_seconds: int
    default_outlook_account: str
    supported_languages: list[str]
    supported_themes: list[str]


class SettingsController:
    def __init__(
        self, settings_service: SettingsService, outlook_service: OutlookService | None = None
    ) -> None:
        self._settings_service = settings_service
        self._outlook_service = outlook_service or OutlookService()

    def get_snapshot(self) -> SettingsSnapshot:
        return SettingsSnapshot(
            company_name=self._settings_service.get_company_name(),
            default_language=self._settings_service.get_default_language(),
            theme_mode=self._settings_service.get_theme_mode(),
            default_delay_seconds=self._settings_service.get_default_delay_seconds(),
            default_outlook_account=self._settings_service.get_default_outlook_account(),
            supported_languages=list(SUPPORTED_LANGUAGES),
            supported_themes=[mode.value for mode in ThemeMode if mode != ThemeMode.SYSTEM],
        )

    def save_general_settings(
        self,
        company_name: str,
        default_language: str,
        default_delay_seconds: int,
        default_outlook_account: str,
    ) -> None:
        self._settings_service.set_company_name(company_name.strip())
        self._settings_service.set_default_language(default_language)
        self._settings_service.set_default_delay_seconds(max(0, default_delay_seconds))
        self._settings_service.set_default_outlook_account(default_outlook_account.strip())

    def set_default_outlook_account(self, smtp_address: str) -> None:
        self._settings_service.set_default_outlook_account(smtp_address.strip())

    def set_theme_mode(self, theme_mode: str) -> None:
        self._settings_service.set_theme_mode(theme_mode)

    def toggle_theme(self) -> str:
        """Flip between Light and Dark, returning the new mode."""
        current = self._settings_service.get_theme_mode()
        new_mode = ThemeMode.LIGHT.value if current == ThemeMode.DARK.value else ThemeMode.DARK.value
        self._settings_service.set_theme_mode(new_mode)
        return new_mode

    # ------------------------------------------------------------------
    # Outlook account detection
    # ------------------------------------------------------------------
    def is_outlook_available(self) -> bool:
        return self._outlook_service.is_available()

    def list_outlook_accounts(self) -> tuple[list[OutlookAccount], str | None]:
        """
        Return `(accounts, error_message)`. `error_message` is set (and
        `accounts` empty) if Outlook couldn't be reached, so the Settings
        page can show a friendly message instead of crashing.
        """
        if not self.is_outlook_available():
            return [], "Outlook Classic automation is only available on Windows."
        try:
            return self._outlook_service.list_accounts(), None
        except OutlookServiceError as exc:
            return [], str(exc)
