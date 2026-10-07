"""后端第 6 阶段：消息响应带回退货快捷选项。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_quick_replies_after_ask_return(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么退货？"}).json()
    labels = _labels(body)
    assert "尺码不合适" in labels
    assert "确认退货" in labels


def test_quick_replies_after_size_reason(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么退货？"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "尺码不合适"}).json()
    labels = _labels(body)
    assert "想换货" in labels
    assert "确认退货" in labels
    assert "转人工" in labels


def test_quick_replies_empty_on_greeting(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "你好"}).json()
    assert body.get("quick_replies") == []


def test_quick_replies_cleared_after_confirm(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么退货？"})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "尺码不合适"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "确认退货"}).json()
    assert body.get("quick_replies") == []
