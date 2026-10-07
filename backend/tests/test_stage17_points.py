"""后端第 17 阶段：会员积分咨询多轮。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_points_clarify_then_balance(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "会员积分"}).json()
    assert t1["source"] == "points_dialogue"
    assert t1["graphic_template_ref"] == "faq:points_clarify"
    assert "积分" in t1["spoken_text"]
    assert len(t1["spoken_text"]) < 45
    assert "查积分" in _labels(t1)

    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查积分"}).json()
    assert t2["graphic_template_ref"] == "faq:points_balance"
    assert not t2["spoken_text"].startswith("查积分")


def test_points_wrong(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "会员积分"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "积分不对"}).json()
    assert t2["graphic_template_ref"] == "faq:points_wrong"
    assert t2["suggest_transfer_human"] is True
    assert not t2["spoken_text"].startswith("积分不对")


def test_points_does_not_steal_warranty(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "保修"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "会员积分"}).json()
    assert body["source"] == "warranty_dialogue"
