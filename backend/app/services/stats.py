"""近程 B1：本地统计汇总（仅验收／联调用，不做现网大盘）。"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import EventRow, SessionRow
from app.services import entries as entries_svc

AGENT_USED = "dh_agent_used"
AGENT_SKIPPED = "dh_agent_skipped"
TRANSFER = "dh_transfer_human"
RATED = "dh_rate"
REPLIED = "dh_message_replied"


def summarize_local_stats(db: Session) -> dict[str, Any]:
    sessions = db.query(SessionRow).all()
    events = db.query(EventRow).all()

    entry_sessions: dict[str, int] = defaultdict(int)
    entry_transferred: dict[str, int] = defaultdict(int)
    session_entry: dict[str, str] = {}
    transferred_sessions = 0
    active_sessions = 0

    for row in sessions:
        session_entry[row.id] = row.entry_id
        entry_sessions[row.entry_id] += 1
        if row.status == "transferred":
            transferred_sessions += 1
            entry_transferred[row.entry_id] += 1
        elif row.status == "active":
            active_sessions += 1

    totals = {
        "agent_used": 0,
        "agent_skipped": 0,
        "transfer_events": 0,
        "ratings": 0,
        "messages_replied": 0,
    }
    entry_agent_used: dict[str, int] = defaultdict(int)
    entry_agent_skipped: dict[str, int] = defaultdict(int)

    for ev in events:
        eid = session_entry.get(ev.session_id, "")
        if ev.event_key == AGENT_USED:
            totals["agent_used"] += 1
            if eid:
                entry_agent_used[eid] += 1
        elif ev.event_key == AGENT_SKIPPED:
            totals["agent_skipped"] += 1
            if eid:
                entry_agent_skipped[eid] += 1
        elif ev.event_key == TRANSFER:
            totals["transfer_events"] += 1
        elif ev.event_key == RATED:
            totals["ratings"] += 1
        elif ev.event_key == REPLIED:
            totals["messages_replied"] += 1

    catalog = {item["id"]: item for item in entries_svc.list_entries()}
    # 保证白名单入口都出现；历史未知入口也列出
    entry_ids = list(catalog.keys())
    for eid in entry_sessions:
        if eid not in entry_ids:
            entry_ids.append(eid)

    by_entry = []
    for eid in entry_ids:
        meta = catalog.get(eid) or {}
        by_entry.append(
            {
                "entry_id": eid,
                "label": str(meta.get("label") or eid),
                "sessions": int(entry_sessions.get(eid, 0)),
                "transferred": int(entry_transferred.get(eid, 0)),
                "agent_used": int(entry_agent_used.get(eid, 0)),
                "agent_skipped": int(entry_agent_skipped.get(eid, 0)),
            }
        )

    return {
        "sessions_total": len(sessions),
        "sessions_active": active_sessions,
        "sessions_transferred": transferred_sessions,
        "transfer_events": totals["transfer_events"],
        "agent_used": totals["agent_used"],
        "agent_skipped": totals["agent_skipped"],
        "messages_replied": totals["messages_replied"],
        "ratings": totals["ratings"],
        "by_entry": by_entry,
    }
