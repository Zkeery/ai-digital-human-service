from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.services import settings_svc
from app.services.sessions import get_session


ALLOWED_RATING_TYPES = {"digital_human", "human", "bot"}


def submit_rating(
    db: Session,
    session_id: str,
    rating_type: str,
    score: int,
    comment: str | None = None,
) -> dict[str, Any]:
    row = get_session(db, session_id)
    if rating_type not in ALLOWED_RATING_TYPES:
        raise AppError("VALIDATION_ERROR", "评价类型仅支持 digital_human／human／bot", status_code=400)
    if score < 1 or score > 5:
        raise AppError("VALIDATION_ERROR", "评分须为 1–5", status_code=400)

    payload: dict[str, Any] = {
        "rating_type": rating_type,
        "score": score,
        "comment": (comment or "")[:200],
        "session_status": row.status,
    }
    if rating_type == "digital_human" and row.last_reply_json:
        payload["last_reply_ref"] = True

    settings_svc.record_event(db, session_id, "dh_rate", payload)
    return {"ok": True, "event_key": "dh_rate"}
