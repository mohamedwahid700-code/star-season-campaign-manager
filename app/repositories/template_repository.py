"""Repository for `Template` records."""

from __future__ import annotations

from app.database.base import session_scope
from app.models.template import Template
from app.repositories.base_repository import BaseRepository


class TemplateRepository(BaseRepository[Template]):
    def __init__(self) -> None:
        super().__init__(Template)

    def get_by_name(self, name: str) -> Template | None:
        with session_scope() as session:
            return session.query(Template).filter(Template.name == name).first()
