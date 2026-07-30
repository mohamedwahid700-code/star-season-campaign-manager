"""
History controller.

Mediates between the History page and `HistoryRepository`. Kept as a
thin controller directly over the repository (no separate service)
since there is no business logic here beyond reading and flattening
already-stored delivery records for display.
"""

from __future__ import annotations

from app.repositories.history_repository import HistoryDetail, HistoryRepository


class HistoryController:
    def __init__(self, history_repository: HistoryRepository | None = None) -> None:
        self._history_repository = history_repository or HistoryRepository()

    def list_history(self) -> list[HistoryDetail]:
        return self._history_repository.get_all_details()
