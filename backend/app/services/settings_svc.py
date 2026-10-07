from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import AppSetting, EventRow, utcnow
from app.services.privacy import redact_payload


SETTING_PILOT = "pilot_entry_id"
SETTING_AGENT = "agent_enabled"
SETTING_RAG = "rag_enabled"


def seed_settings(
    db: Session,
    pilot_entry_id: str,
    agent_enabled: bool,
    rag_enabled: bool = False,
) -> None:
    _upsert(db, SETTING_PILOT, pilot_entry_id)
    _upsert(db, SETTING_AGENT, "1" if agent_enabled else "0")
    _upsert(db, SETTING_RAG, "1" if rag_enabled else "0")
    db.commit()


def get_pilot_entry_id(db: Session, default: str) -> str:
    row = db.get(AppSetting, SETTING_PILOT)
    return row.value if row else default


def get_agent_enabled(db: Session, default: bool) -> bool:
    row = db.get(AppSetting, SETTING_AGENT)
    if row is None:
        return default
    return row.value in {"1", "true", "True", "yes"}


def set_agent_enabled(db: Session, enabled: bool) -> None:
    _upsert(db, SETTING_AGENT, "1" if enabled else "0")
    db.commit()


def get_rag_enabled(db: Session, default: bool) -> bool:
    row = db.get(AppSetting, SETTING_RAG)
    if row is None:
        return default
    return row.value in {"1", "true", "True", "yes"}


def set_rag_enabled(db: Session, enabled: bool) -> None:
    _upsert(db, SETTING_RAG, "1" if enabled else "0")
    db.commit()


def set_pilot_entry_id(db: Session, entry_id: str) -> None:
    _upsert(db, SETTING_PILOT, entry_id)
    db.commit()


def record_event(db: Session, session_id: str, event_key: str, payload: dict[str, Any]) -> EventRow:
    # 不落完整卡号／证件／密码／验证码；text 再截断
    safe = redact_payload(payload)
    if "text" in safe and isinstance(safe["text"], str):
        safe["text"] = safe["text"][:80]
    event = EventRow(
        session_id=session_id,
        event_key=event_key,
        payload_json=json.dumps(safe, ensure_ascii=False),
        created_at=utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(db: Session, session_id: str) -> list[EventRow]:
    return (
        db.query(EventRow)
        .filter(EventRow.session_id == session_id)
        .order_by(EventRow.id.asc())
        .all()
    )


def _upsert(db: Session, key: str, value: str) -> None:
    row = db.get(AppSetting, key)
    if row is None:
        db.add(AppSetting(key=key, value=value, updated_at=utcnow()))
    else:
        row.value = value
        row.updated_at = utcnow()
