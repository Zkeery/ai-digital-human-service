from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    entry_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    guide_shown: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    d_profile_key: Mapped[str | None] = mapped_column(String(8), nullable=True)
    last_reply_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    dialogue_state_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RoomRow(Base):
    __tablename__ = "rooms"

    room_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    d_profile_key: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class StreamCommandRow(Base):
    __tablename__ = "stream_commands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    command_id: Mapped[str] = mapped_column(String(16), nullable=False)
    spoken_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    action_intent: Mapped[str] = mapped_column(String(32), nullable=False, default="none")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="nlp")  # event|nlp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MessageHistoryRow(Base):
    __tablename__ = "message_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EventRow(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    event_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UsageMeter(Base):
    __tablename__ = "usage_meter"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    month_key: Mapped[str] = mapped_column(String(7), unique=True, nullable=False)
    estimated_cny: Mapped[str] = mapped_column(String(32), nullable=False, default="0")
    real_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


def make_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, future=True, connect_args=connect_args)


def make_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def migrate_sqlite_schema(engine) -> None:
    """为已有 SQLite 库补列，避免开发期删库。"""
    if not str(engine.url).startswith("sqlite"):
        return
    with engine.begin() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(sessions)")).fetchall()}
        if cols:
            if "guide_shown" not in cols:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN guide_shown BOOLEAN DEFAULT 0"))
            if "d_profile_key" not in cols:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN d_profile_key VARCHAR(8)"))
            if "last_reply_json" not in cols:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN last_reply_json TEXT"))
            if "dialogue_state_json" not in cols:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN dialogue_state_json TEXT"))
        scols = {row[1] for row in conn.execute(text("PRAGMA table_info(stream_commands)")).fetchall()}
        if scols and "kind" not in scols:
            conn.execute(text("ALTER TABLE stream_commands ADD COLUMN kind VARCHAR(16) DEFAULT 'nlp'"))
