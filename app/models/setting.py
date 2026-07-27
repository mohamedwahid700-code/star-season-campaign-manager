"""Setting model.

A generic key/value store for user-configurable preferences (company
name, theme, language, default delay, default Outlook account, window
size, ...). Using a key/value table -- rather than one column per
setting -- means new settings can be introduced in future sprints
without a schema migration.

`value` is always stored as text; `value_type` tells `SettingsService`
how to deserialize it back into a Python object.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    value: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    value_type: Mapped[str] = mapped_column(String(20), nullable=False, default="string")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"<Setting key={self.key!r} value={self.value!r}>"
