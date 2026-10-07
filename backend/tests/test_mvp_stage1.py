from __future__ import annotations


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_entry_whitelist(client):
    bad = client.post("/api/v1/sessions", json={"entry_id": "other_entry"})
    assert bad.status_code == 403
    assert bad.json()["error"]["code"] == "ENTRY_NOT_ALLOWED"

    ok = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"})
    assert ok.status_code == 200
    assert ok.json()["status"] == "active"


def test_faq_without_agent(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    r = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "你好，请问营业时间？"})
    assert r.status_code == 200
    body = r.json()
    assert body["agent_used"] is False
    assert body["source"] == "branch_dialogue"
    assert "网点" in body["spoken_text"] or "营业" in body["spoken_text"] or "披露" in body["spoken_text"]


def test_finance_greeting_faq_and_branch_hours(client):
    """金融：问候走 FAQ；营业时间走网点多轮。"""
    from app.services.faq import match_faq

    hit = match_faq("你好")
    assert hit is not None
    assert hit["graphic_template_ref"] == "faq:greeting"
    assert "金融" in hit["spoken_text"] or "客服" in hit["spoken_text"]

    assert match_faq("营业时间") is None

    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "营业时间"}).json()
    assert body["source"] == "branch_dialogue"
    assert body["graphic_template_ref"] == "faq:branch_hours"
    assert "大概" not in body["spoken_text"]


def test_ecommerce_sample_no_longer_in_faq(client):
    """电商退货样例已退出 FAQ／路由。"""
    from app.services.faq import match_faq

    assert match_faq("怎么退货？") is None
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么退货？"}).json()
    assert body["source"] != "return_dialogue"
    assert body.get("graphic_template_ref") != "faq:return_reason"


def test_account_balance_path(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查余额"}).json()
    assert t1["source"] == "account_dialogue"
    assert t1["graphic_template_ref"] in {"faq:account_clarify", "faq:account_balance"}


def test_agent_mock_path(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": True})
    r = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "你好"})
    assert r.status_code == 200
    body = r.json()
    assert body["agent_used"] is True
    assert body["source"] == "agent"
    assert "Agent" in body["spoken_text"] or body["spoken_text"]


def test_fallback_event(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    r = client.post(f"/api/v1/sessions/{sid}/fallback")
    assert r.status_code == 200
    events = client.get(f"/api/v1/sessions/{sid}/events").json()
    keys = [e["event_key"] for e in events]
    assert "dh_sync_fallback_2s" in keys


def test_transfer_requires_api(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": True})
    msg = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "我要转人工投诉"}).json()
    assert msg["suggest_transfer_human"] is True
    # 建议不改变状态：仍可继续发消息
    again = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "你好"})
    assert again.status_code == 200

    transferred = client.post(f"/api/v1/sessions/{sid}/transfer").json()
    assert transferred["status"] == "transferred"
    blocked = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "还在吗"})
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "SESSION_NOT_ACTIVE"


def test_persist_across_reconnect(client, tmp_path, monkeypatch):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.post(f"/api/v1/sessions/{sid}/fallback")

    # 新引擎读同一 DB
    from app.core.config import get_settings
    from app.db.models import EventRow, make_engine, make_session_factory

    settings = get_settings()
    engine = make_engine(settings.resolved_database_url())
    SessionLocal = make_session_factory(engine)
    db = SessionLocal()
    try:
        rows = db.query(EventRow).filter(EventRow.session_id == sid).all()
        assert any(r.event_key == "dh_sync_fallback_2s" for r in rows)
    finally:
        db.close()
