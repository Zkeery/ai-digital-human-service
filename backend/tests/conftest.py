from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# 电商样例多轮已归档：跳过对应阶段测试（用边界匹配，避免 stage40 误匹配 stage4）
_ECOM_STAGE_SKIP = pytest.mark.skip(reason="电商样例已归档，路由已关闭")
_ECOM_STAGE_RE = re.compile(r"test_stage(?:[4-9]|1[0-9]|20)(?:_|$|\.)")


def pytest_collection_modifyitems(config, items):
    for item in items:
        name = item.nodeid
        if "test_stage21" in name:
            continue
        if _ECOM_STAGE_RE.search(name) or "test_stage6_quick" in name or "test_stage7_refund" in name:
            item.add_marker(_ECOM_STAGE_SKIP)


# 测试环境：强制 mock，隔离数据目录
@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{data_dir / 'app.db'}")
    monkeypatch.setenv("PILOT_ENTRY_ID", "entry_pilot_001")
    monkeypatch.setenv("AGENT_ENABLED", "0")
    monkeypatch.setenv("RAG_ENABLED", "0")
    monkeypatch.setenv("LLM_MOCK", "1")
    monkeypatch.setenv("LLM_API_KEY", "")

    from app.core.config import get_settings

    get_settings.cache_clear()

    # 重新加载 db 引擎绑定
    import app.db.session as db_session
    from app.core.config import get_settings as gs
    from app.db.models import make_engine, make_session_factory

    settings = gs()
    db_session.engine = make_engine(settings.resolved_database_url())
    db_session.SessionLocal = make_session_factory(db_session.engine)

    from app.main import app

    with TestClient(app) as c:
        yield c

    get_settings.cache_clear()
