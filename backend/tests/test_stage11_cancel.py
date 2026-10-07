"""后端第 11 阶段：取消订单咨询多轮（已发货先挽留）。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_cancel_clarify_then_not_shipped(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "取消订单"}).json()
    assert t1["source"] == "cancel_dialogue"
    assert "还没发货" in _labels(t1)

    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "还没发货"}).json()
    assert t2["graphic_template_ref"] == "faq:cancel_not_shipped"
    assert "取消订单" in t2["spoken_text"]


def test_cancel_shipped_retains_before_howto(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "撤单"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "已经发货"}).json()
    assert t2["graphic_template_ref"] == "faq:cancel_retain"
    assert "拒收" not in t2["spoken_text"]
    assert "还是要取消" in _labels(t2)

    t3 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "还是要取消"}).json()
    assert t3["graphic_template_ref"] == "faq:cancel_shipped_insist"
    assert t3["suggest_transfer_human"] is True
    assert "拒收" in t3["spoken_text"] or "退货" in t3["spoken_text"]


def test_cancel_shipped_wait_keeps_order(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "取消订单"})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "已经发货"})
    t3 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "先等等看"}).json()
    assert t3["graphic_template_ref"] == "faq:cancel_retain_wait"
    assert t3.get("suggest_transfer_human") is False


def test_cancel_does_not_steal_return_flow(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么退货？"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "取消订单"}).json()
    assert body["source"] == "return_dialogue"
    assert body["graphic_template_ref"].startswith("faq:return_reason")
