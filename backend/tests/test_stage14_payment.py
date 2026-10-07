"""后端第 14 阶段：支付与扣款咨询多轮。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_payment_clarify_then_duplicate(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "支付问题"}).json()
    assert t1["source"] == "payment_dialogue"
    assert t1["graphic_template_ref"] == "faq:payment_clarify"
    assert "支付" in t1["spoken_text"]
    assert len(t1["spoken_text"]) < 40
    assert "重复扣款" in _labels(t1)

    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "重复扣款"}).json()
    assert t2["graphic_template_ref"] == "faq:payment_duplicate"
    assert t2["suggest_transfer_human"] is True
    assert not t2["spoken_text"].startswith("重复扣款")


def test_payment_failed_branch(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "支付问题"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "支付失败"}).json()
    assert t2["graphic_template_ref"] == "faq:payment_failed"
    assert "重试" in t2["spoken_text"] or "再试" in t2["spoken_text"]


def test_payment_does_not_steal_refund_flow(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "退款"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "支付问题"}).json()
    assert body["source"] == "refund_dialogue"
