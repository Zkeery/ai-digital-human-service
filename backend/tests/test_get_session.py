"""刷新恢复：GET 会话带回快捷选项。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_get_session_includes_quick_replies_after_clarify(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    ask = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查余额"}).json()
    assert _labels(ask)

    snap = client.get(f"/api/v1/sessions/{sid}").json()
    assert snap["status"] == "active"
    assert snap["last_reply"] is not None
    assert snap["last_reply"]["source"] == "session_restore"
    assert _labels(snap["last_reply"]) == _labels(ask)


def test_get_session_hides_seen_chip_after_answer(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    first = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查余额"}).json()
    assert "怎么查余额" in _labels(first) or any("余额" in x for x in _labels(first))
    # 点一项后再快照，已答项应不再出现（与第32一致）
    pick = _labels(first)[0]
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": pick})
    snap = client.get(f"/api/v1/sessions/{sid}").json()
    restored = _labels(snap["last_reply"] or {})
    assert pick not in restored


def test_get_session_no_last_reply_when_transferred(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查余额"})
    client.post(f"/api/v1/sessions/{sid}/transfer")
    snap = client.get(f"/api/v1/sessions/{sid}").json()
    assert snap["status"] == "transferred"
    assert snap["last_reply"] is None
