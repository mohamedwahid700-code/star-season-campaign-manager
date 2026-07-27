"""
Generic repository base class.

Implements the Repository Pattern: every data-access concern (how a
model is queried, filtered, and persisted) is isolated here so that
services and UI code never construct a SQLAlchemy `Query` directly.
Concrete repositories subclass `BaseRepository[Model]` and add only the
queries that are specific to that model.
"""

from __future__ import annotations

from typing import Generic, Sequence, Type, TypeVar

from app.database.base import session_scope

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Generic CRUD repository for a single SQLAlchemy model.

    Every method opens and closes its own transactional session via
    `session_scope()`, so repositories are safe to call from anywhere
    (UI event handlers, services, background threads) without callers
    needing to manage sessions themselves.
    """

    model: Type[ModelType]

    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model

    def get_by_id(self, record_id: int) -> ModelType | None:
        with session_scope() as session:
            return session.get(self.model, record_id)

    def get_all(self) -> Sequence[ModelType]:
        with session_scope() as session:
            return session.query(self.model).all()

    def add(self, instance: ModelType) -> ModelType:
        with session_scope() as session:
            session.add(instance)
            session.flush()
            session.refresh(instance)
            session.expunge(instance)
            return instance

    def update(self, instance: ModelType) -> ModelType:
        with session_scope() as session:
            merged = session.merge(instance)
            session.flush()
            session.refresh(merged)
            session.expunge(merged)
            return merged

    def delete(self, record_id: int) -> bool:
        with session_scope() as session:
            instance = session.get(self.model, record_id)
            if instance is None:
                return False
            session.delete(instance)
            return True

    def count(self) -> int:
        with session_scope() as session:
            return session.query(self.model).count()
