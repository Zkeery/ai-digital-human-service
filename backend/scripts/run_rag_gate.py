#!/usr/bin/env python3
"""本地跑一遍 C2 RAG 门禁样例（需已安装依赖）。"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

os.environ.setdefault("LLM_MOCK", "1")
os.environ.setdefault("AGENT_ENABLED", "0")
os.environ.setdefault("RAG_ENABLED", "0")


def main() -> int:
    data = tempfile.mkdtemp(prefix="rag-gate-")
    os.environ["DATA_DIR"] = data
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(data) / 'app.db'}"

    from fastapi.testclient import TestClient

    from app.core.config import get_settings
    from app.services import rag_gate

    get_settings.cache_clear()
    import app.db.session as db_session
    from app.db.models import make_engine, make_session_factory
    from app.main import app

    settings = get_settings()
    db_session.engine = make_engine(settings.resolved_database_url())
    db_session.SessionLocal = make_session_factory(db_session.engine)

    failures = []
    with TestClient(app) as client:
        for case in rag_gate.list_cases():
            client.put(
                "/api/v1/config",
                json={"rag_enabled": bool(case.get("rag_enabled", True)), "agent_enabled": False},
            )
            sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()[
                "session_id"
            ]
            body = {"spoken_text": ""}
            for text in case.get("turns") or []:
                body = client.post(
                    f"/api/v1/sessions/{sid}/messages", json={"text": text}
                ).json()
            events = client.get(f"/api/v1/sessions/{sid}/events").json()
            keys = [e["event_key"] for e in events]
            payloads = [e.get("payload") or {} for e in events if e["event_key"] == "dh_rag_hit"]
            errors = rag_gate.evaluate_case_result(
                case=case,
                spoken=body.get("spoken_text") or "",
                event_keys=keys,
                event_payloads=payloads,
            )
            status = "PASS" if not errors else "FAIL"
            print(f"{status} {case['id']} {case.get('title')}")
            if errors:
                for err in errors:
                    print(f"  - {err}")
                failures.append(case["id"])

    print(f"done: {len(rag_gate.list_cases()) - len(failures)}/{len(rag_gate.list_cases())}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
