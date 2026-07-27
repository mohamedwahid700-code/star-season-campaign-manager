"""Repository for `Campaign` records."""

from __future__ import annotations

from app.database.base import session_scope
from app.models.campaign import Campaign, CampaignStatus
from app.repositories.base_repository import BaseRepository


class CampaignRepository(BaseRepository[Campaign]):
    def __init__(self) -> None:
        super().__init__(Campaign)

    def get_by_status(self, status: CampaignStatus) -> list[Campaign]:
        with session_scope() as session:
            return session.query(Campaign).filter(Campaign.status == status).all()

    def get_by_name(self, name: str) -> Campaign | None:
        with session_scope() as session:
            return session.query(Campaign).filter(Campaign.name == name).first()
