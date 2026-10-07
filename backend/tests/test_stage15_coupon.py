"""后端第 15 阶段：优惠券咨询多轮。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_coupon_clarify_then_unusable(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "优惠券"}).json()
    assert t1["source"] == "coupon_dialogue"
    assert t1["graphic_template_ref"] == "faq:coupon_clarify"
    assert "优惠券" in t1["spoken_text"]
    assert len(t1["spoken_text"]) < 40
    assert "用不了" in _labels(t1)

    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "用不了"}).json()
    assert t2["graphic_template_ref"] == "faq:coupon_unusable"
    assert not t2["spoken_text"].startswith("用不了")
    assert t2["suggest_transfer_human"] is True


def test_coupon_missing(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "优惠券"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "找不到券"}).json()
    assert t2["graphic_template_ref"] == "faq:coupon_missing"


def test_coupon_does_not_steal_payment(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "支付问题"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "优惠券"}).json()
    assert body["source"] == "payment_dialogue"
