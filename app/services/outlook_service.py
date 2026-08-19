"""
Outlook integration service (Sprint 3 MVP).

Talks to Outlook Classic exclusively through COM automation via
`pywin32` (`win32com.client`). This is deliberately the only module in
the project that imports `win32com`/`pywintypes`, and it imports them
defensively: on any non-Windows platform, or if pywin32 isn't
installed, `is_available()` returns False and every other method raises
`OutlookNotAvailableError` instead of crashing the app at import time.
This lets the rest of the application (and this Linux/macOS dev
environment) run normally even where Outlook COM automation cannot
exist.

Scope is intentionally narrow, per the Sprint 3 priority reset: detect
accounts, let the user pick one, build a single MailItem with that
account's real signature preserved, preview it, and send exactly one
test email. No bulk sending, no queue, no scheduling.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import pythoncom
    import pywintypes
    import win32com.client

    _PYWIN32_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # noqa: BLE001 - any import failure means "not available"
    pywintypes = None  # type: ignore[assignment]
    win32com = None  # type: ignore[assignment]
    _PYWIN32_IMPORT_ERROR = exc

_OL_MAIL_ITEM = 0  # olMailItem


class OutlookServiceError(Exception):
    """Base class for every error this service raises."""


class OutlookNotAvailableError(OutlookServiceError):
    """Raised when Outlook COM automation cannot be used on this machine at all."""


class OutlookConnectionError(OutlookServiceError):
    """Raised when Outlook itself could not be reached (not installed/not running/COM error)."""


class OutlookSendError(OutlookServiceError):
    """Raised when building or sending a specific email fails."""


@dataclass(frozen=True)
class OutlookAccount:
    """One Outlook Classic account, as detected via COM."""

    display_name: str
    smtp_address: str


@dataclass(frozen=True)
class SendResult:
    """Outcome of a single `send_test_email()` call, ready to log."""

    success: bool
    account: str
    recipient: str
    sent_at: datetime
    error_message: str | None = None


class OutlookService:
    def is_available(self) -> bool:
        """
        Cheap, non-blocking check: is this platform even capable of Outlook
        COM automation? Does not attempt to actually connect to Outlook --
        use `list_accounts()` for that, since a real connection can fail
        even when this check passes (e.g. Outlook not running).
        """
        return sys.platform == "win32" and _PYWIN32_IMPORT_ERROR is None

    def list_accounts(self) -> list[OutlookAccount]:
        """Return every Outlook Classic account configured in the current profile."""
        namespace = self._connect()
        try:
            accounts = []
            for account in namespace.Session.Accounts:
                display_name = str(getattr(account, "DisplayName", "") or "")
                smtp_address = str(getattr(account, "SmtpAddress", "") or "")
                if smtp_address:
                    accounts.append(OutlookAccount(display_name=display_name, smtp_address=smtp_address))
            return accounts
        except Exception as exc:  # noqa: BLE001 - normalize any COM failure
            logger.exception("Failed to enumerate Outlook accounts.")
            raise OutlookConnectionError(f"Could not read Outlook accounts: {exc}") from exc

    def preview_email(self, subject: str, html_body: str, to_email: str, account_smtp: str) -> None:
        """Build a MailItem (with the account's real signature preserved) and show it in Outlook."""
        try:
            self._build_and_display_mail(subject, html_body, to_email, account_smtp)
        except OutlookServiceError:
            raise
        except Exception as exc:  # noqa: BLE001 - normalize any COM failure
            logger.exception("Failed to build preview email.")
            raise OutlookSendError(f"Could not build the preview email: {exc}") from exc

    def send_test_email(self, subject: str, html_body: str, to_email: str, account_smtp: str) -> SendResult:
        """Build a single MailItem (signature preserved) and send it -- exactly one email."""
        sent_at = datetime.now()
        try:
            mail_item = self._build_and_display_mail(subject, html_body, to_email, account_smtp)
            mail_item.Send()
            logger.info(
                "Outlook test email sent. account=%s recipient=%s", account_smtp, to_email
            )
            return SendResult(success=True, account=account_smtp, recipient=to_email, sent_at=sent_at)
        except OutlookServiceError as exc:
            logger.error("Outlook test email failed: %s", exc)
            return SendResult(
                success=False, account=account_smtp, recipient=to_email, sent_at=sent_at,
                error_message=str(exc),
            )
        except Exception as exc:  # noqa: BLE001 - normalize any COM failure
            logger.exception("Outlook test email failed with an unexpected error.")
            return SendResult(
                success=False, account=account_smtp, recipient=to_email, sent_at=sent_at,
                error_message=str(exc),
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _connect(self):
        """Return the Outlook MAPI namespace, raising typed errors on failure."""
        if not self.is_available():
            reason = "not running on Windows" if sys.platform != "win32" else str(_PYWIN32_IMPORT_ERROR)
            raise OutlookNotAvailableError(f"Outlook COM automation is not available here ({reason}).")

        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")
            return namespace
        except Exception as exc:  # noqa: BLE001 - pywintypes.com_error or anything else
            logger.exception("Failed to connect to Outlook via COM.")
            raise OutlookConnectionError(
                f"Could not connect to Outlook: {exc}"
            ) from exc

    def _build_and_display_mail(self, subject: str, html_body: str, to_email: str, account_smtp: str):
        """
        Create a MailItem, assign the chosen sending account, and call
        `.Display()` before touching `HTMLBody`. Outlook only injects the
        account's default signature into a MailItem once it has been
        displayed at least once via automation -- setting `HTMLBody`
        directly never triggers it. Capturing that signature and
        appending it after our own rendered content is what preserves the
        real Outlook signature (task 3/8) for both preview and send.
        """
        namespace = self._connect()

        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail_item = outlook.CreateItem(_OL_MAIL_ITEM)

            account_obj = next(
                (a for a in namespace.Session.Accounts if a.SmtpAddress == account_smtp), None
            )
            if account_obj is None:
                raise OutlookSendError(
                    f"Account '{account_smtp}' was not found in this Outlook profile."
                )
            mail_item._oleobj_.Invoke(*(64209, 0, 8, 0, account_obj))

            mail_item.To = to_email
            mail_item.Subject = subject

            # Triggers Outlook to load this account's default signature
            # into HTMLBody. The window this opens IS the requested
            # "Preview Email" experience (task 9); for a test send it is
            # closed automatically by Outlook once `.Send()` is called.
            mail_item.Display()
            signature_html = mail_item.HTMLBody or ""
            mail_item.HTMLBody = f"{html_body}<br>{signature_html}"

            # Outlook Classic can reset the sending account to the
            # profile default while Display() initializes the Inspector.
            # Reapply the hidden SetSendAccount dispatch method before
            # the preview remains open or the caller invokes Send().
            mail_item._oleobj_.Invoke(*(64209, 0, 8, 0, account_obj))

            return mail_item
        except OutlookServiceError:
            raise
        except Exception as exc:  # noqa: BLE001 - pywintypes.com_error or anything else
            logger.exception("Failed to build Outlook mail item.")
            raise OutlookSendError(f"Could not create the Outlook email: {exc}") from exc
