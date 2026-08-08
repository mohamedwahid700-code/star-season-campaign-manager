"""Repository for `LeadStage` records."""

from __future__ import annotations

from app.database.base import session_scope
from app.models.lead_stage import LeadStage
from app.repositories.base_repository import BaseRepository


class LeadStageRepository(BaseRepository[LeadStage]):
    def __init__(self) -> None:
        super().__init__(LeadStage)

    def get_all_ordered(self) -> list[LeadStage]:
        with session_scope() as session:
            return session.query(LeadStage).order_by(LeadStage.sort_order.asc()).all()

    def get_default(self) -> LeadStage | None:
        """The stage new participants land in (currently seeded as "New")."""
        with session_scope() as session:
            return session.query(LeadStage).filter(LeadStage.is_default.is_(True)).first()

    def get_by_name(self, name: str) -> LeadStage | None:
        with session_scope() as session:
            return session.query(LeadStage).filter(LeadStage.name == name).first()
