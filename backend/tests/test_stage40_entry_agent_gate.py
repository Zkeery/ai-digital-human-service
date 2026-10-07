from app.services import entries as entries_svc


def test_effective_agent_requires_global_and_entry():
    assert entries_svc.effective_agent_enabled(True, "entry_credit_001") is True
    assert entries_svc.effective_agent_enabled(False, "entry_credit_001") is False
    assert entries_svc.effective_agent_enabled(True, "entry_pilot_001") is False
    assert entries_svc.effective_agent_enabled(False, "entry_pilot_001") is False


def test_general_entry_skips_agent_even_when_global_on(client):
    client.put("/api/v1/config", json={"agent_enabled": True})
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    # 无强规则命中的闲聊：总闸开但通用入口默认关 Agent → 不得 dh_agent_used
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "今天天气怎么样啊随便问问"})
    events = client.get(f"/api/v1/sessions/{sid}/events").json()
    keys = [e["event_key"] for e in events]
    assert "dh_agent_used" not in keys
    skipped = [e for e in events if e["event_key"] == "dh_agent_skipped"]
    assert any(e.get("payload", {}).get("reason") == "entry_disabled" for e in skipped)


def test_compose_reply_respects_entry_gate(client):
    client.put("/api/v1/config", json={"agent_enabled": True})
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    res = client.post(
        "/agent/v1/compose-reply",
        json={
            "session_id": sid,
            "user_utterance": "随便聊聊",
            "allow_tools": [],
            "last_visible_messages": [],
        },
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "AGENT_DISABLED"
