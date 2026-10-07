from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.db.models import SessionRow, utcnow
from app.services import account_dialogue
from app.services import auth_dialogue
from app.services import card_dialogue
from app.services import credit_dialogue
from app.services import faq, settings_svc
from app.services import rag as rag_svc
from app.services import transfer_dialogue
from app.services import wealth_dialogue
from app.services import branch_dialogue
from app.services import complaint_dialogue
from app.services.agent import compose_agent_reply
from app.services import history as history_svc
from app.services import return_dialogue


def create_session(db: Session, settings: Settings, entry_id: str) -> SessionRow:
    from app.services import entries as entries_svc

    entries_svc.require_allowed_entry(entry_id)
    row = SessionRow(
        id=str(uuid.uuid4()),
        entry_id=entry_id,
        status="active",
        guide_shown=False,
        d_profile_key=None,
        last_reply_json=None,
        dialogue_state_json=return_dialogue.dump_state(
            {
                "return_flow": "idle",
                "return_reason_category": None,
                "refund_flow": "idle",
                "logistics_flow": "idle",
                "invoice_flow": "idle",
                "address_flow": "idle",
                "cancel_flow": "idle",
                "exchange_flow": "idle",
                "complaint_flow": "idle",
                "complaint_seen": "",
                "payment_flow": "idle",
                "coupon_flow": "idle",
                "warranty_flow": "idle",
                "points_flow": "idle",
                "price_protect_flow": "idle",
                "stock_flow": "idle",
                "account_flow": "idle",
                "account_seen": "",
                "transfer_flow": "idle",
                "transfer_seen": "",
                "card_flow": "idle",
                "card_seen": "",
                "auth_flow": "idle",
                "auth_seen": "",
                "credit_flow": "idle",
                "credit_seen": "",
                "wealth_flow": "idle",
                "wealth_seen": "",
                "branch_flow": "idle",
                "branch_seen": "",
            }
        ),
        created_at=utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    settings_svc.record_event(
        db,
        row.id,
        "dh_session_created",
        {"entry_id": entry_id},
    )
    return row


def get_session(db: Session, session_id: str) -> SessionRow:
    row = db.get(SessionRow, session_id)
    if row is None:
        raise AppError("SESSION_NOT_FOUND", "会话不存在", status_code=404)
    return row


def require_active(row: SessionRow) -> None:
    if row.status != "active":
        raise AppError("SESSION_NOT_ACTIVE", f"会话状态为 {row.status}，不可继续对话", status_code=409)


def handle_message(db: Session, settings: Settings, session_id: str, text: str) -> dict[str, Any]:
    row = get_session(db, session_id)
    require_active(row)

    state = return_dialogue.load_state(row.dialogue_state_json)
    dialogue_reply = None
    work_state = state
    source_reason = "account_dialogue_deterministic"

    # 零售金融多轮：澄清中优先；电商样例路由已关闭
    # 澄清未命中时各场景会释放为 idle 并返回 None，须把 work_state 透传给后续路由
    if work_state.get("account_flow") == "awaiting_clarify":
        dialogue_reply, work_state = account_dialogue.try_account_dialogue(text, work_state)
        source_reason = "account_dialogue_deterministic"
    elif work_state.get("transfer_flow") == "awaiting_clarify":
        dialogue_reply, work_state = transfer_dialogue.try_transfer_dialogue(text, work_state)
        source_reason = "transfer_dialogue_deterministic"
    elif work_state.get("card_flow") == "awaiting_clarify":
        dialogue_reply, work_state = card_dialogue.try_card_dialogue(text, work_state)
        source_reason = "card_dialogue_deterministic"
    elif work_state.get("auth_flow") == "awaiting_clarify":
        dialogue_reply, work_state = auth_dialogue.try_auth_dialogue(text, work_state)
        source_reason = "auth_dialogue_deterministic"
    elif work_state.get("credit_flow") in {"awaiting_clarify", "awaiting_apply"}:
        dialogue_reply, work_state = credit_dialogue.try_credit_dialogue(text, work_state)
        source_reason = "credit_dialogue_deterministic"
    elif work_state.get("wealth_flow") == "awaiting_clarify":
        dialogue_reply, work_state = wealth_dialogue.try_wealth_dialogue(text, work_state)
        source_reason = "wealth_dialogue_deterministic"
    elif work_state.get("branch_flow") == "awaiting_clarify":
        dialogue_reply, work_state = branch_dialogue.try_branch_dialogue(text, work_state)
        source_reason = "branch_dialogue_deterministic"
    elif work_state.get("complaint_flow") == "awaiting_clarify":
        dialogue_reply, work_state = complaint_dialogue.try_complaint_dialogue(text, work_state)
        source_reason = "complaint_dialogue_deterministic"

    if dialogue_reply is None:
        dialogue_reply, work_state = account_dialogue.try_account_dialogue(text, work_state)
        source_reason = "account_dialogue_deterministic"

    if dialogue_reply is None:
        dialogue_reply, work_state = transfer_dialogue.try_transfer_dialogue(text, work_state)
        source_reason = "transfer_dialogue_deterministic"

    if dialogue_reply is None:
        dialogue_reply, work_state = card_dialogue.try_card_dialogue(text, work_state)
        source_reason = "card_dialogue_deterministic"

    if dialogue_reply is None:
        dialogue_reply, work_state = auth_dialogue.try_auth_dialogue(text, work_state)
        source_reason = "auth_dialogue_deterministic"

    if dialogue_reply is None:
        dialogue_reply, work_state = credit_dialogue.try_credit_dialogue(text, work_state)
        source_reason = "credit_dialogue_deterministic"

    if dialogue_reply is None:
        dialogue_reply, work_state = wealth_dialogue.try_wealth_dialogue(text, work_state)
        source_reason = "wealth_dialogue_deterministic"

    if dialogue_reply is None:
        dialogue_reply, work_state = branch_dialogue.try_branch_dialogue(text, work_state)
        source_reason = "branch_dialogue_deterministic"

    if dialogue_reply is None:
        dialogue_reply, work_state = complaint_dialogue.try_complaint_dialogue(text, work_state)
        source_reason = "complaint_dialogue_deterministic"

    new_state = work_state
    from app.services import entries as entries_svc

    global_agent = settings_svc.get_agent_enabled(db, settings.agent_enabled)
    agent_enabled = entries_svc.effective_agent_enabled(global_agent, row.entry_id)
    agent_used = False
    suggest = False

    if dialogue_reply is not None:
        spoken = dialogue_reply["spoken_text"]
        action = dialogue_reply["action_intent"]
        graphic = dialogue_reply["graphic_template_ref"]
        suggest = bool(dialogue_reply.get("suggest_transfer_human", False))
        source = source_reason.replace("_deterministic", "")
        settings_svc.record_event(
            db,
            session_id,
            "dh_agent_skipped",
            {
                "reason": source_reason,
                "account_flow": new_state.get("account_flow"),
                "transfer_flow": new_state.get("transfer_flow"),
                "card_flow": new_state.get("card_flow"),
                "auth_flow": new_state.get("auth_flow"),
                "credit_flow": new_state.get("credit_flow"),
                "wealth_flow": new_state.get("wealth_flow"),
                "branch_flow": new_state.get("branch_flow"),
                "complaint_flow": new_state.get("complaint_flow"),
            },
        )
        row.dialogue_state_json = return_dialogue.dump_state(new_state)
    else:
        aside, aside_source = faq.match_aside(text)
        source = aside_source or "fallback_rule"
        if agent_enabled:
            agent_result = compose_agent_reply(settings, text, aside)
            if agent_result:
                spoken = agent_result["spoken_text"]
                action = agent_result["action_intent"]
                graphic = agent_result["graphic_template_ref"]
                suggest = agent_result["suggest_transfer_human"]
                agent_used = True
                source = "agent"
                settings_svc.record_event(db, session_id, "dh_agent_used", {"suggest_transfer_human": suggest})
            else:
                settings_svc.record_event(db, session_id, "dh_agent_skipped", {"reason": "validate_or_timeout"})
                base = aside or faq.default_fallback_reply()
                spoken = base["spoken_text"]
                action = base["action_intent"]
                graphic = base["graphic_template_ref"]
        else:
            skip_reason = "disabled" if not global_agent else "entry_disabled"
            settings_svc.record_event(db, session_id, "dh_agent_skipped", {"reason": skip_reason})
            base = aside or faq.default_fallback_reply()
            spoken = base["spoken_text"]
            action = base["action_intent"]
            graphic = base["graphic_template_ref"]
        row.dialogue_state_json = return_dialogue.dump_state(new_state)

    rag_on = settings_svc.get_rag_enabled(db, settings.rag_enabled)
    if rag_svc.topic_eligible(text):
        if not rag_on:
            settings_svc.record_event(
                db, session_id, "dh_rag_skip", {"reason": "disabled"}
            )
        else:
            spoken, source, graphic, rag_out = rag_svc.apply_to_reply(
                enabled=True,
                query=text,
                spoken=spoken,
                graphic_template_ref=graphic,
                source=source,
                timeout_seconds=settings.rag_timeout_seconds,
            )
            if rag_out.status == "hit" and rag_out.chunk:
                settings_svc.record_event(
                    db,
                    session_id,
                    "dh_rag_hit",
                    {
                        "chunk_id": rag_out.chunk.get("id"),
                        "collection": rag_out.chunk.get("collection"),
                        "elapsed_ms": rag_out.elapsed_ms,
                    },
                )
            elif rag_out.status == "miss":
                settings_svc.record_event(
                    db, session_id, "dh_rag_miss", {"elapsed_ms": rag_out.elapsed_ms}
                )
            elif rag_out.status == "timeout":
                settings_svc.record_event(
                    db,
                    session_id,
                    "dh_rag_skip",
                    {"reason": "timeout", "elapsed_ms": rag_out.elapsed_ms},
                )

    result = {
        "session_id": session_id,
        "spoken_text": spoken,
        "action_intent": action,
        "graphic_template_ref": graphic,
        "agent_used": agent_used,
        "suggest_transfer_human": suggest,
        "source": source,
        "push_ready": True,
        "sync_hold_ms": settings.sync_hold_ms,
        "quick_replies": return_dialogue.quick_replies_for_state(new_state),
    }
    row.last_reply_json = json.dumps(
        {
            "spoken_text": spoken,
            "action_intent": action,
            "graphic_template_ref": graphic,
        },
        ensure_ascii=False,
    )
    db.commit()
    history_svc.append_message(db, session_id, "user", text, settings.history_limit)
    history_svc.append_message(db, session_id, "assistant", spoken, settings.history_limit)

    settings_svc.record_event(
        db,
        session_id,
        "dh_message_replied",
        {"source": source, "agent_used": agent_used, "text": text},
    )
    return result


def snapshot_last_reply(row: SessionRow, settings: Settings) -> dict[str, Any] | None:
    """供刷新恢复：按当前对话状态重算快捷选项，并附上上次口播摘要。"""
    if row.status != "active":
        return None
    state = return_dialogue.load_state(row.dialogue_state_json)
    chips = return_dialogue.quick_replies_for_state(state)
    base: dict[str, Any] = {}
    if row.last_reply_json:
        try:
            parsed = json.loads(row.last_reply_json)
            if isinstance(parsed, dict):
                base = parsed
        except json.JSONDecodeError:
            base = {}
    if not base and not chips:
        return None
    return {
        "session_id": row.id,
        "spoken_text": str(base.get("spoken_text") or ""),
        "action_intent": str(base.get("action_intent") or "idle"),
        "graphic_template_ref": str(base.get("graphic_template_ref") or "text_card"),
        "agent_used": False,
        "suggest_transfer_human": False,
        "source": "session_restore",
        "push_ready": False,
        "sync_hold_ms": settings.sync_hold_ms,
        "quick_replies": chips,
    }


def mark_fallback(db: Session, session_id: str) -> None:
    row = get_session(db, session_id)
    require_active(row)
    settings_svc.record_event(db, session_id, "dh_sync_fallback_2s", {"reason": "client_timeout_sim"})


def transfer_human(db: Session, session_id: str) -> SessionRow:
    from app.services.digital_human import close_rooms_for_session

    row = get_session(db, session_id)
    require_active(row)
    row.status = "transferred"
    db.commit()
    close_rooms_for_session(db, session_id)
    db.refresh(row)
    settings_svc.record_event(db, session_id, "dh_transfer_human", {"by": "deterministic_api"})
    return row
