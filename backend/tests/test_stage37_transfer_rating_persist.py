"""转人工／评价／降级事件持久化冒烟。"""


def test_transfer_then_rating_and_block_chat(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    ask = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查余额"}).json()
    assert ask["source"] == "account_dialogue"
    assert ask["spoken_text"].strip()

    transferred = client.post(f"/api/v1/sessions/{sid}/transfer").json()
    assert transferred["status"] == "transferred"

    blocked = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "还能问吗"})
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "SESSION_NOT_ACTIVE"

    rated = client.post(
        f"/api/v1/sessions/{sid}/rating",
        json={"rating_type": "digital_human", "score": 5, "comment": "试点评价"},
    ).json()
    assert rated["ok"] is True

    events = client.get(f"/api/v1/sessions/{sid}/events").json()
    keys = [e["event_key"] for e in events]
    assert "dh_transfer_human" in keys
    assert "dh_rate" in keys
    rate_ev = next(e for e in events if e["event_key"] == "dh_rate")
    assert rate_ev["payload"]["score"] == 5
    assert rate_ev["payload"]["rating_type"] == "digital_human"


def test_fallback_and_finance_state_survive_db_reread(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "办信用卡"})
    client.post(f"/api/v1/sessions/{sid}/fallback")

    from app.core.config import get_settings
    from app.db.models import EventRow, SessionRow, make_engine, make_session_factory

    settings = get_settings()
    engine = make_engine(settings.resolved_database_url())
    SessionLocal = make_session_factory(engine)
    db = SessionLocal()
    try:
        row = db.get(SessionRow, sid)
        assert row is not None
        assert row.status == "active"
        assert row.last_reply_json
        assert "credit_flow" in (row.dialogue_state_json or "")
        assert "awaiting_" in (row.dialogue_state_json or "")
        events = db.query(EventRow).filter(EventRow.session_id == sid).all()
        assert any(e.event_key == "dh_sync_fallback_2s" for e in events)
        assert any(e.event_key == "dh_message_replied" for e in events)
    finally:
        db.close()

    # 同库再发消息仍可续聊信用卡澄清
    again = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查额度"}).json()
    assert again["source"] == "credit_dialogue"
    assert again["spoken_text"].strip()


def test_rating_validation(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    bad_type = client.post(
        f"/api/v1/sessions/{sid}/rating",
        json={"rating_type": "unknown_type", "score": 5, "comment": ""},
    )
    assert bad_type.status_code == 400
    assert bad_type.json()["error"]["code"] == "VALIDATION_ERROR"

    bad_score = client.post(
        f"/api/v1/sessions/{sid}/rating",
        json={"rating_type": "digital_human", "score": 9, "comment": ""},
    )
    # 可能被请求模型拦成 422，或服务层 400
    assert bad_score.status_code in {400, 422}
