from app.services import entries as entries_svc


def test_catalog_has_two_finance_entries():
    ids = entries_svc.allowed_entry_ids()
    assert "entry_pilot_001" in ids
    assert "entry_credit_001" in ids
    assert len(ids) >= 2


def test_config_lists_entries(client):
    cfg = client.get("/api/v1/config").json()
    assert "entries" in cfg
    assert len(cfg["entries"]) >= 2
    labels = {e["label"] for e in cfg["entries"]}
    assert "通用金融咨询" in labels
    assert "信用卡专窗" in labels


def test_create_session_on_credit_entry(client):
    res = client.post("/api/v1/sessions", json={"entry_id": "entry_credit_001"})
    assert res.status_code == 200
    body = res.json()
    assert body["entry_id"] == "entry_credit_001"
    assert body["status"] == "active"


def test_unknown_entry_rejected(client):
    res = client.post("/api/v1/sessions", json={"entry_id": "entry_not_exist"})
    assert res.status_code == 403
    err = res.json()["error"]
    assert err["code"] == "ENTRY_NOT_ALLOWED"


def test_set_pilot_entry(client):
    res = client.put("/api/v1/config", json={"pilot_entry_id": "entry_credit_001"})
    assert res.status_code == 200
    assert res.json()["pilot_entry_id"] == "entry_credit_001"
    # 恢复默认，避免影响其他用例顺序依赖
    client.put("/api/v1/config", json={"pilot_entry_id": "entry_pilot_001"})
