"""
Outlook controller.

Mediates between the "Send Test Email" dialog and:
`OutlookService` (account detection, preview, send), `SettingsService`
(the configured default account), and `HistoryRepository` (logging
every test-send attempt: time, account, recipient, success/failure,
error message).
"""

from __future__ import annotations

from app.models.history import DeliveryStatus, History
from app.repositories.history_repository import HistoryRepository
from app.services.outlook_service import OutlookAccount, OutlookService, SendResult
from app.services.settings_service import SettingsService


class OutlookController:
    def __init__(
        self,
        outlook_service: OutlookService | None = None,
        settings_service: SettingsService | None = None,
        history_repository: HistoryRepository | None = None,
    ) -> None:
        self._outlook_service = outlook_service or OutlookService()
        self._settings_service = settings_service or SettingsService()
        self._history_repository = history_repository or HistoryRepository()

    def is_available(self) -> bool:
        return self._outlook_service.is_available()

    def list_accounts(self) -> tuple[list[OutlookAccount], str | None]:
        if not self.is_available():
            return [], "Outlook Classic automation is only available on Windows."
        try:
            return self._outlook_service.list_accounts(), None
        except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
            return [], str(exc)

    def get_default_account(self) -> str:
        return self._settings_service.get_default_outlook_account()

    def preview_email(self, subject: str, html_body: str, to_email: str, account_smtp: str) -> None:
        self._outlook_service.preview_email(subject, html_body, to_email, account_smtp)

    def send_test_email(
        self,
        campaign_id: int,
        contact_id: int,
        subject: str,
        html_body: str,
        to_email: str,
        account_smtp: str,
    ) -> SendResult:
        """Send exactly one test email and log the outcome to History."""
        result = self._outlook_service.send_test_email(subject, html_body, to_email, account_smtp)

        self._history_repository.add(
            History(
                campaign_id=campaign_id,
                contact_id=contact_id,
                subject=subject,
                status=DeliveryStatus.SENT if result.success else DeliveryStatus.FAILED,
                error_message=result.error_message,
                sender_account=account_smtp,
                sent_at=result.sent_at,
            )
        )
        return result
