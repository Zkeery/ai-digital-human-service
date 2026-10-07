"""后端第 27 阶段：网点／营业时间。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_branch_clarify_then_find_keeps_chips(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "网点"}).json()
    assert t1["source"] == "branch_dialogue"
    assert t1["graphic_template_ref"] == "faq:branch_clarify"
    assert "怎么查网点" in _labels(t1)
    assert len(_labels(t1)) <= 5
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么查网点"}).json()
    assert t2["graphic_template_ref"] == "faq:branch_find"
    assert "网点查询" in t2["spoken_text"]
    assert "您还想咨询" in t2["spoken_text"]
    assert "网点营业时间" in _labels(t2)
    assert "客服在线时间" in _labels(t2)
    assert "一般" not in t2["spoken_text"] and "多半" not in t2["spoken_text"] and "大概" not in t2["spoken_text"]


def test_branch_hours_no_promise(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "营业时间"}).json()
    assert t1["graphic_template_ref"] == "faq:branch_hours"
    assert "披露为准" in t1["spoken_text"] or "无法承诺" in t1["spoken_text"]
    assert "您还想咨询" in t1["spoken_text"]
    assert "大概" not in t1["spoken_text"]


def test_branch_where_intent(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "网点在哪"}).json()
    assert body["graphic_template_ref"] == "faq:branch_find"
    assert "网点查询" in body["spoken_text"]
    assert "请问您要查附近网点" not in body["spoken_text"]


def test_branch_does_not_steal_wealth(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "理财"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "网点"}).json()
    assert body["source"] == "wealth_dialogue"
