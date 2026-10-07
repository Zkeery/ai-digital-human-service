"""后端第 26 阶段：理财说明书解读。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_wealth_clarify_then_doc_keeps_chips(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "理财"}).json()
    assert t1["source"] == "wealth_dialogue"
    assert t1["graphic_template_ref"] == "faq:wealth_clarify"
    assert "在哪看说明书" in _labels(t1)
    assert len(_labels(t1)) <= 5
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "在哪看说明书"}).json()
    assert t2["graphic_template_ref"] == "faq:wealth_doc"
    assert "理财" in t2["spoken_text"] or "财富" in t2["spoken_text"]
    assert "说明书" in t2["spoken_text"]
    assert "您还想咨询" in t2["spoken_text"]
    assert "风险等级怎么看" in _labels(t2)
    assert "收益怎么理解" in _labels(t2)
    assert "一般" not in t2["spoken_text"] and "多半" not in t2["spoken_text"]
    t3 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "风险等级怎么看"}).json()
    assert t3["graphic_template_ref"] == "faq:wealth_risk"
    assert "您还想咨询" in t3["spoken_text"]
    assert "收益怎么理解" in _labels(t3)


def test_wealth_yield_no_promise(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "收益怎么理解"}).json()
    assert t1["graphic_template_ref"] == "faq:wealth_yield"
    assert "不等于" in t1["spoken_text"] or "承诺" in t1["spoken_text"]
    assert "您还想咨询" in t1["spoken_text"]
    assert t1["suggest_transfer_human"] is True
    assert "多半" not in t1["spoken_text"]
    assert "在哪看说明书" in _labels(t1)


def test_wealth_does_not_steal_credit(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "信用卡"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "理财"}).json()
    assert body["source"] == "credit_dialogue"
