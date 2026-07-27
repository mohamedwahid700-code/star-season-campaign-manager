"""Repository for `Setting` records.

This repository only understands raw string key/value rows. Type
conversion (str -> int/bool/json) is a business concern that belongs to
`SettingsService`, not to data access.
"""

from __future__ import annotations

from app.database.base import session_scope
from app.models.setting import Setting
from app.repositories.base_repository import BaseRepository


class SettingsRepository(BaseRepository[Setting]):
    def __init__(self) -> None:
        super().__init__(Setting)

    def get_by_key(self, key: str) -> Setting | None:
        with session_scope() as session:
            return session.query(Setting).filter(Setting.key == key).first()

    def upsert(self, key: str, value: str, value_type: str) -> Setting:
        """Insert a setting if it does not exist, otherwise update its value."""
        with session_scope() as session:
            existing = session.query(Setting).filter(Setting.key == key).first()
            if existing is not None:
                existing.value = value
                existing.value_type = value_type
                session.flush()
                session.refresh(existing)
                session.expunge(existing)
                return existing

            new_setting = Setting(key=key, value=value, value_type=value_type)
            session.add(new_setting)
            session.flush()
            session.refresh(new_setting)
            session.expunge(new_setting)
            return new_setting

    def get_all_as_dict(self) -> dict[str, str]:
        with session_scope() as session:
            rows = session.query(Setting).all()
            return {row.key: row.value for row in rows}
