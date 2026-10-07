"""后端第 28 阶段：投诉／纠纷引导（金融）。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_complaint_clarify_then_account_keeps_chips(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "我要投诉"}).json()
    assert t1["source"] == "complaint_dialogue"
    assert t1["graphic_template_ref"] == "faq:complaint_clarify"
    assert "账户交易纠纷" in _labels(t1)
    assert "物流问题" not in _labels(t1)
    assert len(_labels(t1)) <= 5
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "账户交易纠纷"}).json()
    assert t2["graphic_template_ref"] == "faq:complaint_account"
    assert t2["suggest_transfer_human"] is True
    assert "您还想咨询" in t2["spoken_text"]
    assert "卡片额度相关" in _labels(t2)
    assert "服务态度" in _labels(t2)
    assert "一般" not in t2["spoken_text"] and "多半" not in t2["spoken_text"]


def test_complaint_service(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "投诉"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "服务态度"}).json()
    assert t2["graphic_template_ref"] == "faq:complaint_service"
    assert t2["suggest_transfer_human"] is True
    assert not t2["spoken_text"].startswith("服务态度")
    assert "您还想咨询" in t2["spoken_text"]


def test_complaint_can_switch_from_account(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "账户查询"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "我要投诉"}).json()
    assert body["source"] == "complaint_dialogue"
