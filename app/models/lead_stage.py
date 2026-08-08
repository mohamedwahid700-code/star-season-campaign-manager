"""LeadStage model.

A persisted (not hard-coded-enum) pipeline stage that an
`ExhibitionContact` can be in. Kept deliberately minimal for this
milestone: just a name, a display order, and a flag marking which row
is the default new-participant stage ("New"). Full CRM stage-management
(editing/reordering/deleting stages from the UI) is explicitly out of
scope here -- this only exists so ExhibitionContact.lead_stage_id has
somewhere real to point, seeded with one default row.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class LeadStage(Base):
    __tablename__ = "lead_stages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    exhibition_contacts: Mapped[list["ExhibitionContact"]] = relationship(back_populates="lead_stage")

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"<LeadStage id={self.id} name={self.name!r}>"
