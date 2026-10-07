from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.db.models import RoomRow, StreamCommandRow, utcnow
from app.services import settings_svc

ALLOWED_PROFILES = {"001", "002", "003", "004"}
ALLOWED_COMMANDS = {"0001", "0002", "0003", "0004", "0005", "NLP"}
EVENT_COMMANDS = {"0001", "0002", "0003", "0004", "0005"}
ACTION_TO_COMMAND = {
    "none": "NLP",
    "wave": "NLP",
    "nod": "NLP",
    "transfer_announce": "0002",
}


def _session_helpers():
    from app.services import sessions as session_svc

    return session_svc


def show_guide(db: Session, session_id: str) -> dict[str, Any]:
    session_svc = _session_helpers()
    row = session_svc.get_session(db, session_id)
    session_svc.require_active(row)
    if row.guide_shown:
        return {"shown": True, "already_shown": True}
    row.guide_shown = True
    db.commit()
    settings_svc.record_event(db, session_id, "dh_guide_show", {"first": True})
    return {"shown": True, "already_shown": False}


def init_room(db: Session, settings: Settings, session_id: str, d_profile_key: str) -> dict[str, Any]:
    session_svc = _session_helpers()
    row = session_svc.get_session(db, session_id)
    session_svc.require_active(row)
    if d_profile_key not in ALLOWED_PROFILES:
        raise AppError("INVALID_PROFILE", "形象仅支持 001–004", status_code=400)

    existing = (
        db.query(RoomRow)
        .filter(RoomRow.session_id == session_id, RoomRow.status == "active")
        .one_or_none()
    )
    if existing:
        if row.d_profile_key and row.d_profile_key != d_profile_key:
            raise AppError("PROFILE_LOCKED", "会话内形象不可变更", status_code=409)
        return {
            "room_id": existing.room_id,
            "d_profile_key": existing.d_profile_key,
            "reused": True,
            "welcome_command_id": None,
        }

    active_count = db.query(RoomRow).filter(RoomRow.status == "active").count()
    if active_count >= settings.room_active_limit:
        reclaimed = _reclaim_rooms_for_capacity(
            db,
            keep_session_id=session_id,
            limit=settings.room_active_limit,
        )
        active_count = db.query(RoomRow).filter(RoomRow.status == "active").count()
        if reclaimed:
            settings_svc.record_event(
                db,
                session_id,
                "dh_room_reclaimed",
                {"reclaimed": reclaimed, "active_after": active_count},
            )
        if active_count >= settings.room_active_limit:
            raise AppError(
                "ROOM_LIMIT_EXCEEDED",
                f"活跃 Room 已达上限 {settings.room_active_limit}",
                status_code=429,
            )

    room = RoomRow(
        room_id=str(uuid.uuid4()),
        session_id=session_id,
        d_profile_key=d_profile_key,
        status="active",
        created_at=utcnow(),
    )
    row.d_profile_key = d_profile_key
    db.add(room)
    db.commit()
    db.refresh(room)

    welcome = _enqueue_command(
        db,
        room_id=room.room_id,
        session_id=session_id,
        command_id="0001",
        spoken_text="欢迎来到数字人客服，请问有什么可以帮您？",
        action_intent="wave",
        kind="event",
    )
    settings_svc.record_event(
        db,
        session_id,
        "dh_room_init",
        {"room_id": room.room_id, "d_profile_key": d_profile_key},
    )
    return {
        "room_id": room.room_id,
        "d_profile_key": d_profile_key,
        "reused": False,
        "welcome_command_id": welcome.id,
        "sync_hold_ms": settings.sync_hold_ms,
    }


def get_active_room(db: Session, session_id: str) -> RoomRow:
    room = (
        db.query(RoomRow)
        .filter(RoomRow.session_id == session_id, RoomRow.status == "active")
        .one_or_none()
    )
    if room is None:
        raise AppError("ROOM_NOT_FOUND", "请先初始化数字人 Room", status_code=404)
    return room


def push_last_reply(db: Session, session_id: str) -> dict[str, Any]:
    session_svc = _session_helpers()
    row = session_svc.get_session(db, session_id)
    session_svc.require_active(row)
    room = get_active_room(db, session_id)
    if not row.last_reply_json:
        raise AppError("VALIDATION_ERROR", "暂无最近应答可推流，请先发送话术", status_code=400)
    try:
        reply = json.loads(row.last_reply_json)
    except json.JSONDecodeError as exc:
        raise AppError("VALIDATION_ERROR", "最近应答损坏", status_code=500) from exc

    action = reply.get("action_intent", "none")
    command_id = ACTION_TO_COMMAND.get(action)
    if command_id is None or command_id not in ALLOWED_COMMANDS:
        raise AppError("INVALID_COMMAND", f"动作意图不可映射：{action}", status_code=400)

    kind = "event" if command_id in EVENT_COMMANDS else "nlp"
    cmd = _enqueue_command(
        db,
        room_id=room.room_id,
        session_id=session_id,
        command_id=command_id,
        spoken_text=str(reply.get("spoken_text") or ""),
        action_intent=action,
        kind=kind,
    )
    settings_svc.record_event(
        db,
        session_id,
        "dh_stream_queued",
        {"command_db_id": cmd.id, "command_id": command_id, "kind": kind},
    )
    return {
        "command_db_id": cmd.id,
        "command_id": cmd.command_id,
        "status": cmd.status,
        "kind": kind,
        "room_id": room.room_id,
    }


def push_special(
    db: Session,
    session_id: str,
    command_id: str,
    spoken_text: str | None = None,
) -> dict[str, Any]:
    session_svc = _session_helpers()
    row = session_svc.get_session(db, session_id)
    session_svc.require_active(row)
    room = get_active_room(db, session_id)
    if command_id not in EVENT_COMMANDS:
        raise AppError("INVALID_COMMAND", "特殊指令仅支持 0001–0005", status_code=400)
    defaults = {
        "0001": "欢迎语",
        "0002": "正在为您转接人工客服",
        "0003": "当前排队中，请稍候",
        "0004": "系统异常，请稍后重试或转人工",
        "0005": "请查看账单卡片",
    }
    text = spoken_text or defaults.get(command_id, "")
    cmd = _enqueue_command(
        db,
        room_id=room.room_id,
        session_id=session_id,
        command_id=command_id,
        spoken_text=text,
        action_intent="transfer_announce" if command_id == "0002" else "none",
        kind="event",
    )
    settings_svc.record_event(
        db,
        session_id,
        "dh_special_queued",
        {"command_db_id": cmd.id, "command_id": command_id},
    )
    return {
        "command_db_id": cmd.id,
        "command_id": cmd.command_id,
        "status": cmd.status,
        "kind": "event",
        "room_id": room.room_id,
    }


def mark_stream_started(db: Session, session_id: str, command_db_id: int) -> dict[str, Any]:
    session_svc = _session_helpers()
    session_svc.get_session(db, session_id)
    get_active_room(db, session_id)
    cmd = db.get(StreamCommandRow, command_db_id)
    if cmd is None or cmd.session_id != session_id:
        raise AppError("COMMAND_NOT_FOUND", "推流指令不存在", status_code=404)
    cmd.status = "started"
    db.commit()
    db.refresh(cmd)
    settings_svc.record_event(
        db,
        session_id,
        "dh_stream_started",
        {"command_db_id": cmd.id, "command_id": cmd.command_id},
    )
    return {"command_db_id": cmd.id, "status": cmd.status}


def describe_digital_human(db: Session, session_id: str) -> dict[str, Any]:
    session_svc = _session_helpers()
    session_svc.get_session(db, session_id)
    room = (
        db.query(RoomRow)
        .filter(RoomRow.session_id == session_id)
        .order_by(RoomRow.created_at.desc())
        .first()
    )
    commands = (
        db.query(StreamCommandRow)
        .filter(StreamCommandRow.session_id == session_id)
        .order_by(StreamCommandRow.id.desc())
        .limit(20)
        .all()
    )
    return {
        "room": None
        if room is None
        else {
            "room_id": room.room_id,
            "d_profile_key": room.d_profile_key,
            "status": room.status,
        },
        "commands": [
            {
                "command_db_id": c.id,
                "command_id": c.command_id,
                "spoken_text": c.spoken_text,
                "action_intent": c.action_intent,
                "status": c.status,
                "kind": getattr(c, "kind", "nlp"),
            }
            for c in commands
        ],
    }


def close_rooms_for_session(db: Session, session_id: str) -> None:
    rooms = db.query(RoomRow).filter(RoomRow.session_id == session_id, RoomRow.status == "active").all()
    for room in rooms:
        room.status = "closed"
    if rooms:
        db.commit()


def _reclaim_rooms_for_capacity(
    db: Session,
    *,
    keep_session_id: str,
    limit: int,
) -> int:
    """本地手测常刷会话不关 Room。先关已结束会话的 Room；仍满则关最旧的其它活跃 Room。"""
    from app.db.models import SessionRow

    closed = 0
    stale = (
        db.query(RoomRow)
        .join(SessionRow, SessionRow.id == RoomRow.session_id)
        .filter(RoomRow.status == "active", SessionRow.status != "active")
        .all()
    )
    for room in stale:
        room.status = "closed"
        closed += 1
    if closed:
        db.commit()

    active_count = db.query(RoomRow).filter(RoomRow.status == "active").count()
    while active_count >= limit:
        oldest = (
            db.query(RoomRow)
            .filter(RoomRow.status == "active", RoomRow.session_id != keep_session_id)
            .order_by(RoomRow.created_at.asc())
            .first()
        )
        if oldest is None:
            break
        oldest.status = "closed"
        closed += 1
        db.commit()
        active_count = db.query(RoomRow).filter(RoomRow.status == "active").count()
    return closed


def _active_event_blocking(db: Session, session_id: str) -> StreamCommandRow | None:
    """仅「已开始展示」的事件会挡住 NLP（queued 欢迎语不挡联调主路径）。"""
    return (
        db.query(StreamCommandRow)
        .filter(
            StreamCommandRow.session_id == session_id,
            StreamCommandRow.kind == "event",
            StreamCommandRow.status == "started",
        )
        .order_by(StreamCommandRow.id.desc())
        .first()
    )


def _skip_active_events(db: Session, session_id: str) -> None:
    rows = (
        db.query(StreamCommandRow)
        .filter(
            StreamCommandRow.session_id == session_id,
            StreamCommandRow.kind == "event",
            StreamCommandRow.status.in_(("queued", "started")),
        )
        .all()
    )
    for row in rows:
        row.status = "skipped"
    if rows:
        db.commit()


def _enqueue_command(
    db: Session,
    *,
    room_id: str,
    session_id: str,
    command_id: str,
    spoken_text: str,
    action_intent: str,
    kind: str,
) -> StreamCommandRow:
    if command_id not in ALLOWED_COMMANDS:
        raise AppError("INVALID_COMMAND", f"未登记指令 ID：{command_id}", status_code=400)
    if kind == "nlp":
        blocker = _active_event_blocking(db, session_id)
        if blocker is not None:
            raise AppError(
                "BLOCKED_BY_EVENT",
                f"事件指令 {blocker.command_id} 播放中，NLP 不可打断（请先开始展示或推送新事件）",
                status_code=409,
            )
    else:
        # 新事件可打断旧事件
        _skip_active_events(db, session_id)

    cmd = StreamCommandRow(
        room_id=room_id,
        session_id=session_id,
        command_id=command_id,
        spoken_text=spoken_text[:500],
        action_intent=action_intent,
        status="queued",
        kind=kind,
        created_at=utcnow(),
    )
    db.add(cmd)
    db.commit()
    db.refresh(cmd)
    return cmd
