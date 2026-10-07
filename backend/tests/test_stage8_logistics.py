"""后端第 8 阶段：物流发货查询多轮。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_logistics_clarify_then_tracking(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查物流"}).json()
    assert t1["source"] == "logistics_dialogue"
    assert "已经发货" in t1["spoken_text"] or "还没发货" in t1["spoken_text"]
    assert "已经发货查轨迹" in _labels(t1)

    t2 = client.post(
        f"/api/v1/sessions/{sid}/messages", json={"text": "已经发货查轨迹"}
    ).json()
    assert t2["source"] == "logistics_dialogue"
    assert "订单详情" in t2["spoken_text"]
    assert t2.get("quick_replies") == []


def test_logistics_clarify_then_not_shipped(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "快递到哪了"})
    t2 = client.post(
        f"/api/v1/sessions/{sid}/messages", json={"text": "还没发货催一下"}
    ).json()
    assert t2["graphic_template_ref"] == "faq:logistics_not_shipped"
    assert t2["suggest_transfer_human"] is True


def test_logistics_does_not_steal_return_flow(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么退货？"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查物流"}).json()
    # 退货探因中：把「查物流」当原因说明，不切物流流程
    assert body["source"] == "return_dialogue"
    assert body["graphic_template_ref"].startswith("faq:return_reason")
