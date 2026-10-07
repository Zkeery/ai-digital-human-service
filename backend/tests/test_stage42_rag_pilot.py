from app.services import rag as rag_svc


def test_retrieve_hits_branch_hours():
    out = rag_svc.retrieve("网点营业时间几点开门", timeout_seconds=1.0)
    assert out.status == "hit"
    assert out.chunk is not None
    assert out.chunk["id"] == "branch_hours_sample_001"


def test_retrieve_hits_wealth_doc():
    out = rag_svc.retrieve("在哪看理财说明书", timeout_seconds=1.0)
    assert out.status == "hit"
    assert out.chunk is not None
    assert "wealth" in out.chunk["id"]


def test_retrieve_hits_credit_limit():
    rag_svc.load_chunks.cache_clear()
    out = rag_svc.retrieve("查额度", timeout_seconds=1.0)
    assert out.status == "hit"
    assert out.chunk is not None
    assert out.chunk["id"] == "credit_limit_sample_001"


def test_topic_eligible_credit():
    assert rag_svc.topic_eligible("查额度")
    assert rag_svc.topic_eligible("申请材料")
    assert rag_svc.topic_eligible("申请提额")
    assert not rag_svc.topic_eligible("今天天气怎么样")


def test_retrieve_hits_account_balance():
    rag_svc.load_chunks.cache_clear()
    out = rag_svc.retrieve("查余额", timeout_seconds=1.0)
    assert out.status == "hit"
    assert out.chunk is not None
    assert out.chunk["id"] == "account_balance_sample_001"


def test_topic_eligible_account():
    assert rag_svc.topic_eligible("查余额")
    assert rag_svc.topic_eligible("查流水")
    assert rag_svc.topic_eligible("余额对不上")


def test_retrieve_hits_transfer_fail():
    rag_svc.load_chunks.cache_clear()
    out = rag_svc.retrieve("转账失败", timeout_seconds=1.0)
    assert out.status == "hit"
    assert out.chunk is not None
    assert out.chunk["id"] == "transfer_fail_sample_001"


def test_topic_eligible_transfer():
    assert rag_svc.topic_eligible("怎么转账")
    assert rag_svc.topic_eligible("转账失败")
    assert rag_svc.topic_eligible("多久能到")


def test_retrieve_hits_card_loss():
    rag_svc.load_chunks.cache_clear()
    out = rag_svc.retrieve("卡丢了", timeout_seconds=1.0)
    assert out.status == "hit"
    assert out.chunk is not None
    assert out.chunk["id"] == "card_loss_sample_001"


def test_topic_eligible_card():
    assert rag_svc.topic_eligible("怎么绑卡")
    assert rag_svc.topic_eligible("解绑卡片")
    assert rag_svc.topic_eligible("卡丢了")


def test_retrieve_hits_auth_login():
    rag_svc.load_chunks.cache_clear()
    out = rag_svc.retrieve("登录不上", timeout_seconds=1.0)
    assert out.status == "hit"
    assert out.chunk is not None
    assert out.chunk["id"] == "auth_login_sample_001"


def test_retrieve_hits_auth_login_variant_denglu():
    """口语「登陆」与规范「登录」同义，应命中同一登录样例。"""
    rag_svc.load_chunks.cache_clear()
    out = rag_svc.retrieve("登陆不上", timeout_seconds=1.0)
    assert out.status == "hit"
    assert out.chunk is not None
    assert out.chunk["id"] == "auth_login_sample_001"


def test_topic_eligible_auth():
    assert rag_svc.topic_eligible("登录不上")
    assert rag_svc.topic_eligible("登陆不上")
    assert rag_svc.topic_eligible("忘记密码")
    assert rag_svc.topic_eligible("收不到验证码")


def test_retrieve_hits_complaint_account():
    rag_svc.load_chunks.cache_clear()
    out = rag_svc.retrieve("乱扣款", timeout_seconds=1.0)
    assert out.status == "hit"
    assert out.chunk is not None
    assert out.chunk["id"] == "complaint_account_sample_001"


def test_topic_eligible_complaint():
    assert rag_svc.topic_eligible("我要投诉")
    assert rag_svc.topic_eligible("乱扣款")
    assert rag_svc.topic_eligible("服务态度")


def test_retrieve_timeout():
    out = rag_svc.retrieve("网点营业时间", timeout_seconds=0.0)
    assert out.status == "timeout"


def test_rag_off_skips_and_keeps_rule_reply(client):
    client.put("/api/v1/config", json={"rag_enabled": False, "agent_enabled": False})
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    body = client.post(
        f"/api/v1/sessions/{sid}/messages", json={"text": "网点营业时间"}
    ).json()
    assert "样例依据" not in body["spoken_text"]
    assert body["graphic_template_ref"] == "faq:branch_hours"
    events = client.get(f"/api/v1/sessions/{sid}/events").json()
    keys = [e["event_key"] for e in events]
    assert "dh_rag_skip" in keys
    assert "dh_rag_hit" not in keys


def test_rag_on_appends_citation(client):
    client.put("/api/v1/config", json={"rag_enabled": True, "agent_enabled": False})
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    body = client.post(
        f"/api/v1/sessions/{sid}/messages", json={"text": "网点营业时间"}
    ).json()
    assert "样例依据" in body["spoken_text"]
    assert "演示网点" in body["spoken_text"] or "公开演示样例" in body["spoken_text"]
    assert body["graphic_template_ref"] == "faq:branch_hours"
    assert "rag" in body["source"]
    events = client.get(f"/api/v1/sessions/{sid}/events").json()
    hits = [e for e in events if e["event_key"] == "dh_rag_hit"]
    assert hits
    assert hits[0]["payload"].get("chunk_id") == "branch_hours_sample_001"


def test_rag_on_wealth_doc(client):
    client.put("/api/v1/config", json={"rag_enabled": True, "agent_enabled": False})
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "理财"})
    body = client.post(
        f"/api/v1/sessions/{sid}/messages", json={"text": "在哪看说明书"}
    ).json()
    assert body["graphic_template_ref"] == "faq:wealth_doc"
    assert "样例依据" in body["spoken_text"]
    events = client.get(f"/api/v1/sessions/{sid}/events").json()
    assert any(e["event_key"] == "dh_rag_hit" for e in events)


def test_rag_on_credit_limit_citation(client):
    rag_svc.load_chunks.cache_clear()
    client.put("/api/v1/config", json={"rag_enabled": True, "agent_enabled": False})
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_credit_001"}).json()["session_id"]
    body = client.post(
        f"/api/v1/sessions/{sid}/messages", json={"text": "查额度"}
    ).json()
    assert body["graphic_template_ref"] == "faq:credit_limit"
    assert "样例依据" in body["spoken_text"]
    assert "rag" in body["source"]
    events = client.get(f"/api/v1/sessions/{sid}/events").json()
    hits = [e for e in events if e["event_key"] == "dh_rag_hit"]
    assert hits
    assert hits[0]["payload"].get("chunk_id") == "credit_limit_sample_001"


def test_rag_on_account_balance_citation(client):
    rag_svc.load_chunks.cache_clear()
    client.put("/api/v1/config", json={"rag_enabled": True, "agent_enabled": False})
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    body = client.post(
        f"/api/v1/sessions/{sid}/messages", json={"text": "查余额"}
    ).json()
    assert body["graphic_template_ref"] == "faq:account_balance"
    assert "样例依据" in body["spoken_text"]
    assert "rag" in body["source"]
    events = client.get(f"/api/v1/sessions/{sid}/events").json()
    hits = [e for e in events if e["event_key"] == "dh_rag_hit"]
    assert hits
    assert hits[0]["payload"].get("chunk_id") == "account_balance_sample_001"


def test_rag_on_transfer_fail_citation(client):
    rag_svc.load_chunks.cache_clear()
    client.put("/api/v1/config", json={"rag_enabled": True, "agent_enabled": False})
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    body = client.post(
        f"/api/v1/sessions/{sid}/messages", json={"text": "转账失败"}
    ).json()
    assert body["graphic_template_ref"] == "faq:transfer_fail"
    assert "样例依据" in body["spoken_text"]
    assert "rag" in body["source"]
    events = client.get(f"/api/v1/sessions/{sid}/events").json()
    hits = [e for e in events if e["event_key"] == "dh_rag_hit"]
    assert hits
    assert hits[0]["payload"].get("chunk_id") == "transfer_fail_sample_001"


def test_rag_on_card_bind_citation(client):
    rag_svc.load_chunks.cache_clear()
    client.put("/api/v1/config", json={"rag_enabled": True, "agent_enabled": False})
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    body = client.post(
        f"/api/v1/sessions/{sid}/messages", json={"text": "怎么绑卡"}
    ).json()
    assert body["graphic_template_ref"] == "faq:card_bind"
    assert "样例依据" in body["spoken_text"]
    assert "rag" in body["source"]
    events = client.get(f"/api/v1/sessions/{sid}/events").json()
    hits = [e for e in events if e["event_key"] == "dh_rag_hit"]
    assert hits
    assert hits[0]["payload"].get("chunk_id") == "card_bind_sample_001"


def test_rag_on_auth_login_citation(client):
    rag_svc.load_chunks.cache_clear()
    client.put("/api/v1/config", json={"rag_enabled": True, "agent_enabled": False})
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    body = client.post(
        f"/api/v1/sessions/{sid}/messages", json={"text": "登录不上"}
    ).json()
    assert body["graphic_template_ref"] == "faq:auth_login"
    assert "样例依据" in body["spoken_text"]
    assert "rag" in body["source"]
    events = client.get(f"/api/v1/sessions/{sid}/events").json()
    hits = [e for e in events if e["event_key"] == "dh_rag_hit"]
    assert hits
    assert hits[0]["payload"].get("chunk_id") == "auth_login_sample_001"


def test_rag_on_complaint_account_citation(client):
    rag_svc.load_chunks.cache_clear()
    client.put("/api/v1/config", json={"rag_enabled": True, "agent_enabled": False})
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    body = client.post(
        f"/api/v1/sessions/{sid}/messages", json={"text": "我要投诉乱扣款"}
    ).json()
    assert body["graphic_template_ref"] == "faq:complaint_account"
    assert "样例依据" in body["spoken_text"]
    assert "rag" in body["source"]
    events = client.get(f"/api/v1/sessions/{sid}/events").json()
    hits = [e for e in events if e["event_key"] == "dh_rag_hit"]
    assert hits
    assert hits[0]["payload"].get("chunk_id") == "complaint_account_sample_001"


def test_config_rag_toggle(client):
    off = client.put("/api/v1/config", json={"rag_enabled": False}).json()
    assert off["rag_enabled"] is False
    on = client.put("/api/v1/config", json={"rag_enabled": True}).json()
    assert on["rag_enabled"] is True
    got = client.get("/api/v1/config").json()
    assert got["rag_enabled"] is True
