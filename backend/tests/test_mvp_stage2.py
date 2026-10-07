from __future__ import annotations


def _sid(client):
    return client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]


def test_guide_once(client):
    sid = _sid(client)
    first = client.post(f"/api/v1/sessions/{sid}/guide")
    assert first.status_code == 200
    assert first.json()["already_shown"] is False
    second = client.post(f"/api/v1/sessions/{sid}/guide")
    assert second.json()["already_shown"] is True
    keys = [e["event_key"] for e in client.get(f"/api/v1/sessions/{sid}/events").json()]
    assert keys.count("dh_guide_show") == 1


def test_init_and_profile_lock(client):
    sid = _sid(client)
    bad = client.post(f"/api/v1/sessions/{sid}/digital-human/init", json={"d_profile_key": "999"})
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "INVALID_PROFILE"

    ok = client.post(f"/api/v1/sessions/{sid}/digital-human/init", json={"d_profile_key": "001"})
    assert ok.status_code == 200
    assert ok.json()["room_id"]
    assert ok.json()["reused"] is False

    locked = client.post(f"/api/v1/sessions/{sid}/digital-human/init", json={"d_profile_key": "002"})
    assert locked.status_code == 409
    assert locked.json()["error"]["code"] == "PROFILE_LOCKED"

    reuse = client.post(f"/api/v1/sessions/{sid}/digital-human/init", json={"d_profile_key": "001"})
    assert reuse.status_code == 200
    assert reuse.json()["reused"] is True


def test_room_limit_reclaims_oldest(client, monkeypatch):
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("ROOM_ACTIVE_LIMIT", "1")
    get_settings.cache_clear()
    settings = get_settings()
    object.__setattr__(settings, "room_active_limit", 1)

    sid1 = _sid(client)
    first = client.post(f"/api/v1/sessions/{sid1}/digital-human/init", json={"d_profile_key": "001"})
    assert first.status_code == 200
    room1 = first.json()["room_id"]

    sid2 = _sid(client)
    second = client.post(f"/api/v1/sessions/{sid2}/digital-human/init", json={"d_profile_key": "001"})
    assert second.status_code == 200
    assert second.json()["room_id"] != room1

    info1 = client.get(f"/api/v1/sessions/{sid1}/digital-human").json()
    assert info1["room"] is None or info1["room"]["status"] != "active"


def test_push_and_stream_started(client):
    sid = _sid(client)
    client.post(f"/api/v1/sessions/{sid}/digital-human/init", json={"d_profile_key": "001"})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "你好"})
    pushed = client.post(f"/api/v1/sessions/{sid}/digital-human/push")
    assert pushed.status_code == 200
    cmd_id = pushed.json()["command_db_id"]
    started = client.post(
        f"/api/v1/sessions/{sid}/digital-human/stream-started",
        json={"command_db_id": cmd_id},
    )
    assert started.status_code == 200
    assert started.json()["status"] == "started"
    info = client.get(f"/api/v1/sessions/{sid}/digital-human").json()
    assert info["room"]["status"] == "active"
    assert any(c["status"] == "started" for c in info["commands"])


def test_compose_reply_respects_agent_switch(client):
    sid = _sid(client)
    client.put("/api/v1/config", json={"agent_enabled": False})
    disabled = client.post(
        "/agent/v1/compose-reply",
        json={"session_id": sid, "user_utterance": "你好"},
    )
    assert disabled.status_code == 409
    client.put("/api/v1/config", json={"agent_enabled": True})
    ok = client.post(
        "/agent/v1/compose-reply",
        json={"session_id": sid, "user_utterance": "你好", "last_visible_messages": ["hi"]},
    )
    assert ok.status_code == 200
    assert ok.json()["agent_used"] is True


def test_rating_and_transfer_closes_room(client):
    sid = _sid(client)
    client.post(f"/api/v1/sessions/{sid}/digital-human/init", json={"d_profile_key": "003"})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "营业时间"})
    rate = client.post(
        f"/api/v1/sessions/{sid}/rating",
        json={"rating_type": "digital_human", "score": 5, "comment": "清楚"},
    )
    assert rate.status_code == 200
    keys = [e["event_key"] for e in client.get(f"/api/v1/sessions/{sid}/events").json()]
    assert "dh_rate" in keys

    client.post(f"/api/v1/sessions/{sid}/transfer")
    info = client.get(f"/api/v1/sessions/{sid}/digital-human").json()
    assert info["room"]["status"] == "closed"
    push = client.post(f"/api/v1/sessions/{sid}/digital-human/push")
    assert push.status_code == 409
