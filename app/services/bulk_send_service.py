"""
Bulk send service.

Orchestrates sending one campaign to many contacts. Reuses
`OutlookService.send_test_email()` as the per-email primitive
unchanged -- it already builds the MailItem, assigns the chosen
account, preserves that account's real signature, and sends -- so the
exact, already-verified send mechanism is used for every recipient,
not a separate/duplicated code path.

This service is intentionally free of any Tkinter or threading
concerns: it is a plain, synchronous, callback-driven loop. The caller
(`BulkSendController`) is responsible for running it on a background
thread and marshaling `on_progress` callbacks back onto the UI thread,
so this module stays simple to test and reason about in isolation.

Pause is implemented as a blocking wait on `pause_event` between
sends (never mid-send); cancel is checked before every send and during
the inter-send delay, so cancelling stops promptly without leaving a
send half-done.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Literal

from app.models.campaign import Campaign
from app.models.contact import Contact
from app.models.history import DeliveryStatus, History
from app.repositories.history_repository import HistoryRepository
from app.services.outlook_service import OutlookService
from app.services.template_rendering_service import TemplateRenderingService

logger = logging.getLogger(__name__)

BulkSendEventKind = Literal["sending", "sent", "failed", "done", "cancelled"]

# How often (seconds) the pause-wait and the inter-send delay re-check
# for a cancel request, so cancelling never has to wait out a long delay.
_POLL_INTERVAL_SECONDS = 0.2


@dataclass(frozen=True)
class BulkSendEvent:
    kind: BulkSendEventKind
    index: int          # 1-based position of the contact just processed/being processed
    total: int
    contact: Contact | None
    sent_count: int
    failed_count: int
    error_message: str = ""


@dataclass(frozen=True)
class BulkSendSummary:
    total: int
    sent_count: int
    failed_count: int
    cancelled: bool


class BulkSendService:
    def __init__(
        self,
        outlook_service: OutlookService | None = None,
        history_repository: HistoryRepository | None = None,
        rendering_service: TemplateRenderingService | None = None,
    ) -> None:
        self._outlook_service = outlook_service or OutlookService()
        self._history_repository = history_repository or HistoryRepository()
        self._rendering_service = rendering_service or TemplateRenderingService()

    def send_campaign(
        self,
        campaign: Campaign,
        contacts: list[Contact],
        account_smtp: str,
        delay_seconds: float,
        pause_event: threading.Event,
        cancel_event: threading.Event,
        on_progress: Callable[[BulkSendEvent], None],
    ) -> BulkSendSummary:
        """
        Send `campaign` to every contact in `contacts`, one at a time.

        Safe to call directly (e.g. in tests) without a real thread --
        it simply runs to completion or until `cancel_event` is set.
        """
        total = len(contacts)
        sent_count = 0
        failed_count = 0

        for index, contact in enumerate(contacts, start=1):
            if cancel_event.is_set():
                on_progress(
                    BulkSendEvent("cancelled", index, total, None, sent_count, failed_count)
                )
                return BulkSendSummary(total, sent_count, failed_count, cancelled=True)

            self._wait_while_paused(pause_event, cancel_event)
            if cancel_event.is_set():
                on_progress(
                    BulkSendEvent("cancelled", index, total, None, sent_count, failed_count)
                )
                return BulkSendSummary(total, sent_count, failed_count, cancelled=True)

            on_progress(BulkSendEvent("sending", index, total, contact, sent_count, failed_count))

            subject = self._rendering_service.render(campaign.subject, contact, campaign)
            html_body = self._rendering_service.render(campaign.html_body, contact, campaign)

            result = self._outlook_service.send_test_email(subject, html_body, contact.email, account_smtp)

            self._history_repository.add(
                History(
                    campaign_id=campaign.id,
                    contact_id=contact.id,
                    subject=subject,
                    status=DeliveryStatus.SENT if result.success else DeliveryStatus.FAILED,
                    error_message=result.error_message,
                    sender_account=account_smtp,
                    sent_at=result.sent_at,
                )
            )

            if result.success:
                sent_count += 1
                on_progress(BulkSendEvent("sent", index, total, contact, sent_count, failed_count))
            else:
                failed_count += 1
                on_progress(
                    BulkSendEvent(
                        "failed", index, total, contact, sent_count, failed_count,
                        error_message=result.error_message,
                    )
                )

            if index < total and delay_seconds > 0:
                if self._sleep_with_cancel_check(delay_seconds, cancel_event):
                    on_progress(
                        BulkSendEvent("cancelled", index, total, None, sent_count, failed_count)
                    )
                    return BulkSendSummary(total, sent_count, failed_count, cancelled=True)

        on_progress(BulkSendEvent("done", total, total, None, sent_count, failed_count))
        return BulkSendSummary(total, sent_count, failed_count, cancelled=False)

    @staticmethod
    def _wait_while_paused(pause_event: threading.Event, cancel_event: threading.Event) -> None:
        while pause_event.is_set() and not cancel_event.is_set():
            time.sleep(_POLL_INTERVAL_SECONDS)

    @staticmethod
    def _sleep_with_cancel_check(duration_seconds: float, cancel_event: threading.Event) -> bool:
        """Sleep in small increments so a cancel request is honored promptly. Returns True if cancelled."""
        elapsed = 0.0
        while elapsed < duration_seconds:
            if cancel_event.is_set():
                return True
            step = min(_POLL_INTERVAL_SECONDS, duration_seconds - elapsed)
            time.sleep(step)
            elapsed += step
        return False
