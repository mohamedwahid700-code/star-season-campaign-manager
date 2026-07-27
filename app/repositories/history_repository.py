"""Repository for `History` records."""

from __future__ import annotations

from app.database.base import session_scope
from app.models.history import DeliveryStatus, History
from app.repositories.base_repository import BaseRepository


class HistoryRepository(BaseRepository[History]):
    def __init__(self) -> None:
        super().__init__(History)

    def get_by_campaign(self, campaign_id: int) -> list[History]:
        with session_scope() as session:
            return session.query(History).filter(History.campaign_id == campaign_id).all()

    def get_by_status(self, status: DeliveryStatus) -> list[History]:
        with session_scope() as session:
            return session.query(History).filter(History.status == status).all()
