"""后端第 23 阶段：银行卡绑定／解绑／挂失引导。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_card_clarify_then_bind(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "银行卡"}).json()
    assert t1["source"] == "card_dialogue"
    assert t1["graphic_template_ref"] == "faq:card_clarify"
    assert "怎么绑卡" in _labels(t1)
    assert len(_labels(t1)) <= 5
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么绑卡"}).json()
    assert t2["graphic_template_ref"] == "faq:card_bind"
    assert not t2["spoken_text"].startswith("怎么绑卡")


def test_card_loss(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "挂失"}).json()
    assert t1["graphic_template_ref"] == "faq:card_loss"
    assert t1["suggest_transfer_human"] is True
    assert "完整卡号" in t1["spoken_text"] or "不能替您挂失" in t1["spoken_text"]


def test_card_does_not_steal_transfer(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "转账"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "银行卡"}).json()
    assert body["source"] == "transfer_dialogue"
