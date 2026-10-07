"""后端第 24 阶段：登录／密码／验证码引导。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_auth_password_direct(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "忘记密码"}).json()
    assert t1["source"] == "auth_dialogue"
    assert t1["graphic_template_ref"] == "faq:auth_password"
    assert "密码" in t1["spoken_text"]
    assert "请勿" in t1["spoken_text"] or "不要" in t1["spoken_text"] or "别" in t1["spoken_text"]


def test_auth_login_accepts_denglu_variant(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False, "rag_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "登陆不上"}).json()
    assert t1["source"] == "auth_dialogue"
    assert t1["graphic_template_ref"] == "faq:auth_login"


def test_auth_clarify_then_otp(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "登录问题"}).json()
    assert t1["graphic_template_ref"] == "faq:auth_clarify"
    assert "收不到验证码" in _labels(t1)
    assert len(_labels(t1)) <= 5
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "收不到验证码"}).json()
    assert t2["graphic_template_ref"] == "faq:auth_otp"
    assert t2["suggest_transfer_human"] is True


def test_auth_can_switch_from_card(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "银行卡"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "忘记密码"}).json()
    assert body["source"] == "auth_dialogue"
