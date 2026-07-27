"""Repository for `Blacklist` records."""

from __future__ import annotations

from app.database.base import session_scope
from app.models.blacklist import Blacklist
from app.repositories.base_repository import BaseRepository


class BlacklistRepository(BaseRepository[Blacklist]):
    def __init__(self) -> None:
        super().__init__(Blacklist)

    def is_blacklisted(self, email: str) -> bool:
        with session_scope() as session:
            return (
                session.query(Blacklist).filter(Blacklist.email == email).first()
                is not None
            )

    def get_by_email(self, email: str) -> Blacklist | None:
        with session_scope() as session:
            return session.query(Blacklist).filter(Blacklist.email == email).first()
