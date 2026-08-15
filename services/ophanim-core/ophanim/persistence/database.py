"""Database connection and session factory for Ophanim Core persistence."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


def create_db_engine(database_url: str = "sqlite:///:memory:", echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine configured for Ophanim Core."""
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(database_url, echo=echo, connect_args=connect_args)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a session factory bound to the given engine."""
    return sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


def init_db(engine: Engine) -> None:
    """Initialize database tables using declarative metadata."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Context manager providing a transactional session."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
