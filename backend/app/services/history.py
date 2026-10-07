from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.db.models import MessageHistoryRow, utcnow
from app.services.privacy import redact_sensitive


def append_message(db: Session, session_id: str, role: str, text: str, limit: int) -> None:
    # 仅用户原文脱敏；助手口播常含「密码、信用卡」列举，不可误伤
    stored = text or ""
    if role == "user":
        stored = redact_sensitive(stored)
    db.add(
        MessageHistoryRow(
            session_id=session_id,
            role=role,
            text=stored[:200],
            created_at=utcnow(),
        )
    )
    db.commit()
    # 裁剪超出 limit 的旧记录（按条，一轮约 2 条，这里按条数 limit*2）
    keep = max(limit * 2, 2)
    rows = (
        db.query(MessageHistoryRow)
        .filter(MessageHistoryRow.session_id == session_id)
        .order_by(MessageHistoryRow.id.desc())
        .all()
    )
    for old in rows[keep:]:
        db.delete(old)
    db.commit()


def list_history(db: Session, session_id: str, limit: int) -> list[dict[str, Any]]:
    rows = (
        db.query(MessageHistoryRow)
        .filter(MessageHistoryRow.session_id == session_id)
        .order_by(MessageHistoryRow.id.desc())
        .limit(max(limit * 2, 2))
        .all()
    )
    rows = list(reversed(rows))
    return [
        {
            "id": r.id,
            "role": r.role,
            "text": r.text,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
