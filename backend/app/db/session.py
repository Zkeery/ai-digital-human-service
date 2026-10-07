from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Base, make_engine, make_session_factory, migrate_sqlite_schema

_settings = get_settings()
engine = make_engine(_settings.resolved_database_url())
SessionLocal = make_session_factory(engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    migrate_sqlite_schema(engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
