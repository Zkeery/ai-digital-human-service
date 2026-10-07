"""后端第 12 阶段：换货咨询多轮。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_exchange_clarify_then_size(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "换货"}).json()
    assert t1["source"] == "exchange_dialogue"
    assert t1["graphic_template_ref"] == "faq:exchange_clarify"
    assert "尺码不合适" in _labels(t1)

    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "尺码不合适"}).json()
    assert t2["graphic_template_ref"] == "faq:exchange_size"
    assert "换货" in t2["spoken_text"]


def test_exchange_wrong_item(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "申请换货"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "发错货了"}).json()
    assert t2["graphic_template_ref"] == "faq:exchange_wrong"
    assert t2["suggest_transfer_human"] is True


def test_exchange_does_not_steal_return_mid_flow(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么退货？"})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "尺码不合适"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "想换货"}).json()
    assert body["source"] == "return_dialogue"
    assert body["graphic_template_ref"] == "faq:return_exchange"
