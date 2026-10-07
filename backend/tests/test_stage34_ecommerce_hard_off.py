"""电商多轮残留硬下线。"""

import json

from app.services import return_dialogue


def test_load_state_forces_ecommerce_idle():
    raw = json.dumps(
        {
            "return_flow": "awaiting_reason",
            "return_reason_category": "size",
            "refund_flow": "awaiting_clarify",
            "logistics_flow": "awaiting_clarify",
            "coupon_flow": "awaiting_clarify",
            "account_flow": "awaiting_clarify",
            "account_seen": "balance",
        },
        ensure_ascii=False,
    )
    state = return_dialogue.load_state(raw)
    assert state["return_flow"] == "idle"
    assert state["return_reason_category"] is None
    assert state["refund_flow"] == "idle"
    assert state["logistics_flow"] == "idle"
    assert state["coupon_flow"] == "idle"
    assert state["account_flow"] == "awaiting_clarify"
    assert state["account_seen"] == "balance"


def test_stale_ecommerce_state_yields_no_ecommerce_chips():
    chips = return_dialogue.quick_replies_for_state(
        {
            "refund_flow": "awaiting_clarify",
            "return_flow": "awaiting_reason",
            "account_flow": "idle",
        }
    )
    assert chips == []
    labels = " ".join(c["label"] for c in chips)
    assert "退货" not in labels
    assert "退款" not in labels


def test_try_return_dialogue_disabled():
    reply, new_state = return_dialogue.try_return_dialogue(
        "怎么退货",
        {"return_flow": "idle", "refund_flow": "awaiting_clarify"},
    )
    assert reply is None
    assert new_state["return_flow"] == "idle"
    assert new_state["refund_flow"] == "idle"


def test_stale_ecommerce_session_gets_offtopic(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    from app.db.models import SessionRow
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        row = db.get(SessionRow, sid)
        dirty = json.loads(row.dialogue_state_json)
        dirty["refund_flow"] = "awaiting_clarify"
        dirty["return_flow"] = "awaiting_reason"
        row.dialogue_state_json = json.dumps(dirty, ensure_ascii=False)
        db.commit()
    finally:
        db.close()

    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查退款进度"}).json()
    assert body["source"] != "return_dialogue"
    assert body["source"] == "offtopic_rule"
    assert not any("寄回" in (c.get("label") or "") for c in body.get("quick_replies") or [])
