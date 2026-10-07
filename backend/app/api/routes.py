from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.schemas.api import (
    ComposeReplyRequest,
    ConfigUpdate,
    ConfigView,
    CreateSessionRequest,
    CreateSessionResponse,
    EntryView,
    EventItem,
    InitDigitalHumanRequest,
    MessageRequest,
    MessageResponse,
    RatingRequest,
    SessionSnapshotResponse,
    SessionStatusResponse,
    SpecialCommandRequest,
    StatsView,
    StreamStartedRequest,
)
from app.services import contract_aliases
from app.services import digital_human as dh_svc
from app.services import entries as entries_svc
from app.services import faq
from app.services import history as history_svc
from app.services import rating as rating_svc
from app.services import sessions as session_svc
from app.services import settings_svc
from app.services import stats as stats_svc
from app.services import sync_watch
from app.services.agent import compose_agent_reply

router = APIRouter(prefix="/api/v1")
agent_router = APIRouter(prefix="/agent/v1")


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ai-digital-human-cs"}


@router.get("/config", response_model=ConfigView)
def read_config(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> ConfigView:
    pilot = settings_svc.get_pilot_entry_id(db, settings.pilot_entry_id)
    # 默认入口必须在白名单内；历史脏值回退到目录第一项
    if pilot not in entries_svc.allowed_entry_ids():
        pilot = entries_svc.list_entries()[0]["id"]
    return ConfigView(
        pilot_entry_id=pilot,
        agent_enabled=settings_svc.get_agent_enabled(db, settings.agent_enabled),
        rag_enabled=settings_svc.get_rag_enabled(db, settings.rag_enabled),
        llm_mock=settings.llm_mock,
        monthly_budget_cny=settings.monthly_budget_cny,
        room_active_limit=settings.room_active_limit,
        sync_hold_ms=settings.sync_hold_ms,
        entries=[EntryView(**item) for item in entries_svc.list_entries()],
    )


@router.put("/config", response_model=ConfigView)
def update_config(
    body: ConfigUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ConfigView:
    if body.agent_enabled is not None:
        settings_svc.set_agent_enabled(db, body.agent_enabled)
    if body.rag_enabled is not None:
        settings_svc.set_rag_enabled(db, body.rag_enabled)
    if body.pilot_entry_id is not None:
        entries_svc.require_allowed_entry(body.pilot_entry_id)
        settings_svc.set_pilot_entry_id(db, body.pilot_entry_id)
    return read_config(db=db, settings=settings)


@router.get("/stats", response_model=StatsView)
def read_stats(db: Session = Depends(get_db)) -> StatsView:
    """本地会话／事件汇总；前端仅验收模式请求。"""
    return StatsView(**stats_svc.summarize_local_stats(db))


@router.post("/sessions", response_model=CreateSessionResponse)
def create_session(
    body: CreateSessionRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CreateSessionResponse:
    row = session_svc.create_session(db, settings, body.entry_id)
    return CreateSessionResponse(session_id=row.id, entry_id=row.entry_id, status=row.status)


@router.get("/sessions/{session_id}", response_model=SessionSnapshotResponse)
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SessionSnapshotResponse:
    row = session_svc.get_session(db, session_id)
    last = session_svc.snapshot_last_reply(row, settings)
    return SessionSnapshotResponse(
        session_id=row.id,
        entry_id=row.entry_id,
        status=row.status,
        last_reply=MessageResponse(**last) if last else None,
    )


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
def post_message(
    session_id: str,
    body: MessageRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    result = session_svc.handle_message(db, settings, session_id, body.text)
    return MessageResponse(**result)


@router.post("/sessions/{session_id}/fallback")
def post_fallback(session_id: str, db: Session = Depends(get_db)) -> dict:
    session_svc.mark_fallback(db, session_id)
    return {"ok": True, "event_key": "dh_sync_fallback_2s"}


@router.post("/sessions/{session_id}/transfer", response_model=SessionStatusResponse)
def post_transfer(session_id: str, db: Session = Depends(get_db)) -> SessionStatusResponse:
    row = session_svc.transfer_human(db, session_id)
    return SessionStatusResponse(session_id=row.id, entry_id=row.entry_id, status=row.status)


@router.post("/sessions/{session_id}/guide")
def post_guide(session_id: str, db: Session = Depends(get_db)) -> dict:
    return dh_svc.show_guide(db, session_id)


@router.post("/sessions/{session_id}/digital-human/init")
def post_dh_init(
    session_id: str,
    body: InitDigitalHumanRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    return dh_svc.init_room(db, settings, session_id, body.d_profile_key)


@router.post("/sessions/{session_id}/digital-human/push")
def post_dh_push(session_id: str, db: Session = Depends(get_db)) -> dict:
    return dh_svc.push_last_reply(db, session_id)


@router.post("/sessions/{session_id}/digital-human/special")
def post_dh_special(session_id: str, body: SpecialCommandRequest, db: Session = Depends(get_db)) -> dict:
    return dh_svc.push_special(db, session_id, body.command_id, body.spoken_text)


@router.post("/sessions/{session_id}/digital-human/check-sync")
def post_dh_check_sync(
    session_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    return sync_watch.check_sync_fallback(db, settings, session_id)


@router.get("/sessions/{session_id}/history")
def get_history(
    session_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    session_svc.get_session(db, session_id)
    return {"items": history_svc.list_history(db, session_id, settings.history_limit)}


@router.get("/contract/aliases")
def get_aliases() -> dict:
    return contract_aliases.list_aliases()


@router.get("/themes")
def get_themes() -> dict:
    return contract_aliases.list_themes()


@router.post("/sessions/{session_id}/digital-human/stream-started")
def post_dh_started(session_id: str, body: StreamStartedRequest, db: Session = Depends(get_db)) -> dict:
    return dh_svc.mark_stream_started(db, session_id, body.command_db_id)


@router.get("/sessions/{session_id}/digital-human")
def get_dh(session_id: str, db: Session = Depends(get_db)) -> dict:
    return dh_svc.describe_digital_human(db, session_id)


@router.post("/sessions/{session_id}/rating")
def post_rating(session_id: str, body: RatingRequest, db: Session = Depends(get_db)) -> dict:
    return rating_svc.submit_rating(db, session_id, body.rating_type, body.score, body.comment)


@router.get("/sessions/{session_id}/events", response_model=list[EventItem])
def get_events(session_id: str, db: Session = Depends(get_db)) -> list[EventItem]:
    session_svc.get_session(db, session_id)
    items = []
    for ev in settings_svc.list_events(db, session_id):
        try:
            payload = json.loads(ev.payload_json)
        except json.JSONDecodeError:
            payload = {}
        items.append(
            EventItem(
                id=ev.id,
                session_id=ev.session_id,
                event_key=ev.event_key,
                payload=payload,
                created_at=ev.created_at.isoformat(),
            )
        )
    return items


@agent_router.post("/compose-reply")
def compose_reply(
    body: ComposeReplyRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    row = session_svc.get_session(db, body.session_id)
    global_agent = settings_svc.get_agent_enabled(db, settings.agent_enabled)
    if not entries_svc.effective_agent_enabled(global_agent, row.entry_id):
        raise AppError("AGENT_DISABLED", "Agent 旁路已关闭（总闸或本入口未启用）", status_code=409)
    if body.allow_tools:
        raise AppError("VALIDATION_ERROR", "本阶段不允许外部工具", status_code=400)

    faq_hit = body.faq_hit
    aside_source: str | None = None
    if faq_hit is None:
        faq_hit, aside_source = faq.match_aside(body.user_utterance)
    # last_visible_messages 仅作上下文截断记录，不落原文全量
    _ = [m[:80] for m in body.last_visible_messages[:5]]
    result = compose_agent_reply(settings, body.user_utterance, faq_hit)
    if result is None:
        base = faq_hit or faq.default_fallback_reply()
        settings_svc.record_event(db, body.session_id, "dh_agent_skipped", {"reason": "compose_failed"})
        if aside_source:
            source = aside_source
        elif faq_hit:
            source = "faq"
        else:
            source = "fallback_rule"
        return {
            "spoken_text": base["spoken_text"],
            "action_intent": base["action_intent"],
            "graphic_template_ref": base["graphic_template_ref"],
            "suggest_transfer_human": False,
            "safety_flags": [],
            "agent_used": False,
            "source": source,
        }
    settings_svc.record_event(db, body.session_id, "dh_agent_used", {"via": "compose-reply"})
    return {**result, "agent_used": True, "source": "agent"}
