"""Repository for `Exhibition` records."""

from __future__ import annotations

from app.database.base import session_scope
from app.models.exhibition import Exhibition
from app.repositories.base_repository import BaseRepository


class ExhibitionRepository(BaseRepository[Exhibition]):
    def __init__(self) -> None:
        super().__init__(Exhibition)

    def get_all_ordered(self) -> list[Exhibition]:
        """Every exhibition, most recently updated first."""
        with session_scope() as session:
            return session.query(Exhibition).order_by(Exhibition.updated_at.desc()).all()
