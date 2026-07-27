"""
SQLAlchemy engine and session management.

Every other module that needs database access imports `SessionLocal`
(or, preferably, goes through a repository) from here. There is a single
engine per process, created lazily so that importing this module never
has side effects on its own -- side effects only occur when the engine
is actually requested.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.app_config import get_config


class Base(DeclarativeBase):
    """Declarative base class shared by every ORM model in the application."""
    pass


_engine: Engine | None = None
_SessionFactory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Return the process-wide SQLAlchemy engine, creating it on first use."""
    global _engine
    if _engine is None:
        config = get_config()
        connect_args = {}
        if config.database_url.startswith("sqlite"):
            # Required for SQLite when the same connection may be touched
            # from different threads (the Tkinter mainloop vs. background
            # worker threads used for sending campaigns in later sprints).
            connect_args["check_same_thread"] = False

        _engine = create_engine(
            config.database_url,
            echo=False,
            future=True,
            connect_args=connect_args,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return the process-wide session factory, creating it on first use."""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _SessionFactory


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of operations.

    Usage:
        with session_scope() as session:
            session.add(obj)

    Commits on success, rolls back on exception, and always closes the
    session. Repositories should use this instead of managing sessions
    manually so transaction handling stays consistent across the codebase.
    """
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
