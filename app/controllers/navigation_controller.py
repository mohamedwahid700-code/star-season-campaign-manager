"""
Navigation controller.

Owns the single piece of state that matters for page routing: which
`NavigationKey` is currently active. The main window subscribes to
changes and swaps the visible view; the sidebar calls `navigate_to()`
when a nav button is clicked. Neither of them needs to know about the
other, which keeps the sidebar, top bar, and content area independently
replaceable in future sprints.
"""

from __future__ import annotations

import logging
from typing import Callable

from app.config.constants import NavigationKey

logger = logging.getLogger(__name__)

NavigationCallback = Callable[[NavigationKey], None]


class NavigationController:
    def __init__(self, initial_key: NavigationKey = NavigationKey.DASHBOARD) -> None:
        self._current_key: NavigationKey = initial_key
        self._subscribers: list[NavigationCallback] = []

    @property
    def current_key(self) -> NavigationKey:
        return self._current_key

    def subscribe(self, callback: NavigationCallback) -> None:
        self._subscribers.append(callback)

    def unsubscribe(self, callback: NavigationCallback) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def clear_subscribers(self) -> None:
        """Drop every subscriber. Used when the UI is rebuilt (e.g. a theme
        toggle destroys and recreates the sidebar) so a stale callback bound
        to an already-destroyed widget is never invoked again."""
        self._subscribers.clear()

    def navigate_to(self, key: NavigationKey) -> None:
        if key == self._current_key:
            return
        logger.debug("Navigating from %s to %s", self._current_key.value, key.value)
        self._current_key = key
        for callback in list(self._subscribers):
            callback(key)
