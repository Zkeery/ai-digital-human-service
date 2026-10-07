"""后端第 25 阶段：信用卡／额度／还款日。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_credit_clarify_then_limit(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "信用卡"}).json()
    assert t1["source"] == "credit_dialogue"
    assert t1["graphic_template_ref"] == "faq:credit_clarify"
    assert "办卡申请" in _labels(t1)
    assert "查额度" in _labels(t1)
    assert len(_labels(t1)) <= 5
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查额度"}).json()
    assert t2["graphic_template_ref"] == "faq:credit_limit"
    assert not t2["spoken_text"].startswith("查额度")
    assert "信用卡" in t2["spoken_text"] and "可用额度" in t2["spoken_text"]
    assert "您还想咨询" in t2["spoken_text"]
    assert "还款与账单" in _labels(t2)
    assert "一般" not in t2["spoken_text"] and "多半" not in t2["spoken_text"]


def test_credit_apply_opens_series_popup(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "我想办信用卡"}).json()
    assert t1["source"] == "credit_dialogue"
    assert t1["graphic_template_ref"] == "faq:credit_apply_clarify"
    assert "卡种怎么选" in _labels(t1)
    assert "申请材料" in _labels(t1)
    assert "申请步骤" in _labels(t1)
    assert "查额度" not in _labels(t1)
    assert "申请提额" not in _labels(t1)
    assert len(_labels(t1)) <= 5

    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "申请步骤"}).json()
    assert t2["graphic_template_ref"] == "faq:credit_apply_steps"
    assert "申请办卡" in t2["spoken_text"] or "卡片申请" in t2["spoken_text"]
    assert "不能代办" in t2["spoken_text"]
    assert "卡种怎么选" in _labels(t2) or "申请材料" in _labels(t2)


def test_credit_raise(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "申请提额"}).json()
    assert t1["graphic_template_ref"] == "faq:credit_raise"
    assert t1["suggest_transfer_human"] is True
    assert "审核" in t1["spoken_text"]
    assert "保证不了" not in t1["spoken_text"]
    assert "多半" not in t1["spoken_text"]


def test_credit_does_not_steal_auth(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "登录问题"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "信用卡"}).json()
    assert body["source"] == "auth_dialogue"
