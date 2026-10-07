"""偏题／电商关键词友好兜底。"""


def test_ecommerce_keywords_get_finance_boundary(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    for text in ("怎么退货？", "查物流", "优惠券用不了", "我要价保"):
        body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": text}).json()
        assert body["source"] == "offtopic_rule", text
        assert "零售金融" in body["spoken_text"]
        assert body["graphic_template_ref"] == "faq:offtopic_ecommerce"


def test_unknown_gets_friendly_fallback(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "今天天气怎么样"}).json()
    assert body["source"] == "fallback_rule"
    assert "查余额" in body["spoken_text"] or "办信用卡" in body["spoken_text"]
    assert "零售金融" in body["spoken_text"]


def test_greeting_is_retail_finance(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "你好"}).json()
    assert body["source"] == "faq"
    assert "零售金融" in body["spoken_text"]
