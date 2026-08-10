"""
Bulk send controller.

Mediates between the Send Campaign UI (recipient picker -> confirm ->
progress dialog) and `BulkSendService`. Owns the background thread the
actual sending runs on, plus the `threading.Event`s used for
pause/cancel and the thread-safe `queue.Queue` the progress dialog
polls from the main thread via `after()` -- Tkinter widgets must only
ever be touched from the main thread, so no code here (or in
`BulkSendService`) touches the UI directly.

COM initialization: Outlook COM automation requires
`pythoncom.CoInitialize()` to have been called on whichever OS thread
makes the COM calls. The main Tkinter thread gets this for free (Test
Email, which runs on a button-click handler, works without any extra
setup) -- but a plain `threading.Thread`, like the one this controller
spawns, does not inherit that, and every COM call on it fails with a
connection error until it initializes COM for itself. That mismatch
was the actual root cause of Send Campaign failing with "Could not
connect to Outlook" on every attempt while Send Test Email worked
perfectly: the background thread was never CoInitialize()'d.
"""

from __future__ import annotations

import logging
import queue
import threading

from app.models.campaign import Campaign
from app.models.contact import Contact
from app.services.bulk_send_service import BulkSendEvent, BulkSendService, BulkSendSummary

logger = logging.getLogger(__name__)

try:
    import pythoncom

    _PYTHONCOM_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only on non-Windows dev machines
    pythoncom = None  # type: ignore[assignment]
    _PYTHONCOM_AVAILABLE = False


class BulkSendController:
    def __init__(self, bulk_send_service: BulkSendService | None = None) -> None:
        self._service = bulk_send_service or BulkSendService()
        self._thread: threading.Thread | None = None
        self._pause_event = threading.Event()
        self._cancel_event = threading.Event()
        self._events: queue.Queue[BulkSendEvent] = queue.Queue()
        self._summary: BulkSendSummary | None = None

    def start(
        self,
        campaign: Campaign,
        contacts: list[Contact],
        account_smtps: list[str],
        delay_seconds: float,
    ) -> None:
        """Start sending on a background thread. Only one send runs at a time per controller instance.

        `account_smtps` is one or more sender accounts; with more than
        one, `BulkSendService` distributes recipients round-robin.
        """
        self._pause_event.clear()
        self._cancel_event.clear()
        self._summary = None

        def _run() -> None:
            # This thread is brand new and has never touched COM, so
            # Outlook automation must be initialized here before any
            # send happens -- see the module docstring for why.
            if _PYTHONCOM_AVAILABLE:
                pythoncom.CoInitialize()
            try:
                summary = self._service.send_campaign(
                    campaign=campaign,
                    contacts=contacts,
                    account_smtps=account_smtps,
                    delay_seconds=delay_seconds,
                    pause_event=self._pause_event,
                    cancel_event=self._cancel_event,
                    on_progress=self._events.put,
                )
                self._summary = summary
            except Exception:  # noqa: BLE001 - never let the worker thread die silently
                logger.exception("Bulk send worker thread crashed unexpectedly.")
                raise
            finally:
                if _PYTHONCOM_AVAILABLE:
                    pythoncom.CoUninitialize()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def pause(self) -> None:
        self._pause_event.set()

    def resume(self) -> None:
        self._pause_event.clear()

    def cancel(self) -> None:
        self._cancel_event.set()
        # A cancel during a paused send would otherwise wait forever on
        # the pause loop; clearing pause lets the service notice the
        # cancel flag on its next poll immediately.
        self._pause_event.clear()

    def is_paused(self) -> bool:
        return self._pause_event.is_set()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def get_summary(self) -> BulkSendSummary | None:
        """Available once the background thread has finished (success or cancelled)."""
        return self._summary

    def poll_events(self) -> list[BulkSendEvent]:
        """Drain and return every event queued since the last call. Safe to call from the main thread only."""
        events: list[BulkSendEvent] = []
        while True:
            try:
                events.append(self._events.get_nowait())
            except queue.Empty:
                break
        return events
