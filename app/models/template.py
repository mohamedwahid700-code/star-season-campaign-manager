"""Template model.

Represents a reusable HTML email template. Rendering (Jinja2) and the
template editor arrive in a later sprint; this sprint only defines the
storage schema.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)

    html_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    thumbnail_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="template")

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"<Template id={self.id} name={self.name!r}>"
