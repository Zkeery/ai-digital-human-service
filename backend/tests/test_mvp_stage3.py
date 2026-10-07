from __future__ import annotations

import time


def _sid(client):
    return client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]


def test_history_after_messages(client):
    sid = _sid(client)
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "你好"})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "营业时间"})
    hist = client.get(f"/api/v1/sessions/{sid}/history").json()["items"]
    assert len(hist) >= 4
    assert hist[0]["role"] in {"user", "assistant"}


def test_check_sync_timeout(client, monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    object.__setattr__(settings, "sync_hold_ms", 30)

    sid = _sid(client)
    client.post(f"/api/v1/sessions/{sid}/digital-human/init", json={"d_profile_key": "001"})
    # 欢迎语 queued，直接检查超时
    time.sleep(0.05)
    r = client.post(f"/api/v1/sessions/{sid}/digital-human/check-sync")
    assert r.status_code == 200
    body = r.json()
    assert body["fallback"] is True
    keys = [e["event_key"] for e in client.get(f"/api/v1/sessions/{sid}/events").json()]
    assert "dh_sync_fallback_2s" in keys


def test_nlp_blocked_by_started_event(client):
    sid = _sid(client)
    init = client.post(f"/api/v1/sessions/{sid}/digital-human/init", json={"d_profile_key": "001"}).json()
    welcome_id = init["welcome_command_id"]
    client.post(
        f"/api/v1/sessions/{sid}/digital-human/stream-started",
        json={"command_db_id": welcome_id},
    )
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "你好"})
    blocked = client.post(f"/api/v1/sessions/{sid}/digital-human/push")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "BLOCKED_BY_EVENT"


def test_special_command(client):
    sid = _sid(client)
    client.post(f"/api/v1/sessions/{sid}/digital-human/init", json={"d_profile_key": "002"})
    r = client.post(
        f"/api/v1/sessions/{sid}/digital-human/special",
        json={"command_id": "0002"},
    )
    assert r.status_code == 200
    assert r.json()["command_id"] == "0002"
    assert r.json()["kind"] == "event"


def test_aliases_and_themes(client):
    aliases = client.get("/api/v1/contract/aliases").json()
    assert aliases["aliases"]
    themes = client.get("/api/v1/themes").json()
    assert len(themes["themes"]) >= 2
