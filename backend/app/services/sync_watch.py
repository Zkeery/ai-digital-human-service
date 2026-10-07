from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.db.models import StreamCommandRow
from app.services import settings_svc
from app.services.digital_human import get_active_room


def check_sync_fallback(db: Session, settings: Settings, session_id: str) -> dict[str, Any]:
    """若最近 queued 指令超过 hold 仍未 started，则记 2s 降级。"""
    from app.services.sessions import get_session, require_active

    row = get_session(db, session_id)
    require_active(row)
    get_active_room(db, session_id)

    cmd = (
        db.query(StreamCommandRow)
        .filter(
            StreamCommandRow.session_id == session_id,
            StreamCommandRow.status == "queued",
        )
        .order_by(StreamCommandRow.id.desc())
        .first()
    )
    if cmd is None:
        return {"fallback": False, "reason": "no_queued_command"}

    created = cmd.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    elapsed_ms = (datetime.now(timezone.utc) - created).total_seconds() * 1000
    if elapsed_ms < settings.sync_hold_ms:
        return {
            "fallback": False,
            "reason": "not_expired",
            "elapsed_ms": int(elapsed_ms),
            "hold_ms": settings.sync_hold_ms,
            "command_db_id": cmd.id,
        }

    settings_svc.record_event(
        db,
        session_id,
        "dh_sync_fallback_2s",
        {
            "reason": "auto_check_sync",
            "command_db_id": cmd.id,
            "elapsed_ms": int(elapsed_ms),
        },
    )
    cmd.status = "skipped"
    db.commit()
    return {
        "fallback": True,
        "reason": "timeout",
        "elapsed_ms": int(elapsed_ms),
        "command_db_id": cmd.id,
        "event_key": "dh_sync_fallback_2s",
    }
