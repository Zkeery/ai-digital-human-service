#!/usr/bin/env python3
"""金融 Agent 旁路真实模型冒烟（需 LLM_API_KEY，LLM_MOCK=0）。"""

from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

# 刻意避开确定性金融关键词，走 Agent／FAQ 旁路
SAMPLES = [
    "你们数字人客服能帮我做什么？",
    "我想先了解你们能咨询哪些业务，不要推销产品。",
    "如果我说不清楚问题该怎么办？",
]

OUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "evidence"
    / "后端阶段31-金融Agent真实冒烟"
)


def main() -> None:
    settings = get_settings()
    get_settings.cache_clear()
    settings = get_settings()

    meta = {
        "llm_mock": settings.llm_mock,
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "has_key": bool(settings.llm_api_key),
    }
    if settings.llm_mock or not settings.llm_api_key:
        raise SystemExit(
            "需要真实冒烟：请在 .env 设置 LLM_MOCK=0 且配置 LLM_API_KEY（勿提交密钥）"
        )

    client = TestClient(app)
    client.put("/api/v1/config", json={"agent_enabled": True})

    rows: list[dict] = []
    for text in SAMPLES:
        sid = client.post(
            "/api/v1/sessions", json={"entry_id": "entry_pilot_001"}
        ).json()["session_id"]
        t0 = time.perf_counter()
        body = client.post(
            f"/api/v1/sessions/{sid}/messages", json={"text": text}
        ).json()
        ms = int((time.perf_counter() - t0) * 1000)
        spoken = body.get("spoken_text") or ""
        mockish = "Agent 旁路已润色" in spoken
        rows.append(
            {
                "user": text,
                "spoken_text": spoken,
                "source": body.get("source"),
                "agent_used": body.get("agent_used"),
                "action_intent": body.get("action_intent"),
                "graphic_template_ref": body.get("graphic_template_ref"),
                "suggest_transfer_human": body.get("suggest_transfer_human"),
                "elapsed_ms": ms,
                "structure_ok": bool(spoken.strip()),
                "likely_mock": mockish,
            }
        )

    client.put("/api/v1/config", json={"agent_enabled": False})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "smoke.json").write_text(
        json.dumps({"meta": meta, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    ok = sum(1 for r in rows if r["agent_used"] and r["structure_ok"] and not r["likely_mock"])
    lines = [
        "# 金融 Agent 真实冒烟记录",
        "",
        f"- 模型：`{meta['llm_model']}` @ `{meta['llm_base_url']}`",
        f"- LLM_MOCK：`{meta['llm_mock']}`；有 Key：是",
        f"- 成功真实 Agent 条数：{ok}/{len(rows)}",
        "",
        "## 样例",
        "",
    ]
    for i, r in enumerate(rows, 1):
        lines.extend(
            [
                f"### A{i}",
                "",
                f"- 用户：{r['user']}",
                f"- 口播：{r['spoken_text']}",
                f"- source=`{r['source']}` agent_used=`{r['agent_used']}` "
                f"耗时={r['elapsed_ms']}ms 疑似mock=`{r['likely_mock']}`",
                f"- 动作=`{r['action_intent']}` 建议转人工=`{r['suggest_transfer_human']}` "
                f"图文=`{r['graphic_template_ref']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## 产品经理确认",
            "",
            "待确认：口播是否可接受（可回复「按推荐」）。",
            "",
        ]
    )
    (OUT_DIR / "smoke.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"ok": ok, "total": len(rows), "out": str(OUT_DIR)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
