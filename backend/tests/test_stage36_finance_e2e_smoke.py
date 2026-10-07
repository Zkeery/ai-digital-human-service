"""金融 P0／P1 入口端到端冒烟：每场景首句进对路由，无电商回潮。"""

CASES = [
    ("查余额", "account_dialogue"),
    ("转账失败", "transfer_dialogue"),
    ("怎么绑卡", "card_dialogue"),
    ("登录不上", "auth_dialogue"),
    ("办信用卡", "credit_dialogue"),
    ("理财说明书", "wealth_dialogue"),
    ("网点在哪", "branch_dialogue"),
    ("我要投诉", "complaint_dialogue"),
]


def test_finance_p0_p1_entry_routes(client):
    client.put("/api/v1/config", json={"agent_enabled": False})
    for text, expect_source in CASES:
        sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
        body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": text}).json()
        assert body["source"] == expect_source, (text, body["source"], body.get("spoken_text", "")[:60])
        assert body["spoken_text"].strip()
        assert "退货" not in body["spoken_text"]
        assert "物流" not in body["spoken_text"]
        labels = " ".join(c.get("label", "") for c in body.get("quick_replies") or [])
        assert "寄回" not in labels
        assert "优惠券" not in labels


def test_finance_e2e_aside_and_privacy(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    off = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么退货"}).json()
    assert off["source"] == "offtopic_rule"
    hi = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "你好"}).json()
    assert hi["source"] == "faq"
    assert "零售金融" in hi["spoken_text"]
    card = client.post(
        f"/api/v1/sessions/{sid}/messages",
        json={"text": "卡号6222021234567890123怎么绑"},
    ).json()
    assert card["source"] == "card_dialogue"
    assert "已脱敏" not in card["spoken_text"]
    assert "6222021234567890123" not in card["spoken_text"]
