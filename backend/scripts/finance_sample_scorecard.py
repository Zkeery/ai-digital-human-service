#!/usr/bin/env python3
"""生成金融话术样例打分表（确定性多轮，无需真实模型 Key）。"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

SAMPLES: list[dict[str, str]] = [
    {"id": "S01", "scene": "账户", "text": "查余额"},
    {"id": "S02", "scene": "转账", "text": "转账失败"},
    {"id": "S03", "scene": "银行卡", "text": "银行卡"},
    {"id": "S04", "scene": "登录", "text": "登录不上"},
    {"id": "S05", "scene": "信用卡", "text": "信用卡"},
    {"id": "S06", "scene": "信用卡-额度", "text": "查额度", "after": "信用卡"},
    {"id": "S07", "scene": "理财", "text": "理财"},
    {"id": "S08", "scene": "理财-收益", "text": "收益怎么理解"},
    {"id": "S09", "scene": "网点", "text": "网点"},
    {"id": "S10", "scene": "投诉", "text": "我要投诉"},
]

OUT = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "evidence"
    / "后端阶段30-金融话术样例打分"
    / "scorecard.md"
)


def _run() -> list[dict[str, object]]:
    client = TestClient(app)
    client.put("/api/v1/config", json={"agent_enabled": False})
    rows: list[dict[str, object]] = []
    for sample in SAMPLES:
        sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()[
            "session_id"
        ]
        if sample.get("after"):
            client.post(
                f"/api/v1/sessions/{sid}/messages",
                json={"text": sample["after"]},
            )
        body = client.post(
            f"/api/v1/sessions/{sid}/messages",
            json={"text": sample["text"]},
        ).json()
        chips = [c.get("label") for c in (body.get("quick_replies") or [])]
        rows.append(
            {
                "id": sample["id"],
                "scene": sample["scene"],
                "user": sample["text"]
                if not sample.get("after")
                else f"{sample['after']} → {sample['text']}",
                "spoken": body.get("spoken_text", ""),
                "graphic": body.get("graphic_template_ref", ""),
                "source": body.get("source", ""),
                "chips": chips,
                "suggest_transfer": bool(body.get("suggest_transfer_human")),
            }
        )
    return rows


def _md(rows: list[dict[str, object]]) -> str:
    lines = [
        "# 金融话术样例打分表",
        "",
        "> 生成自 `backend/scripts/finance_sample_scorecard.py`（确定性多轮，Agent 关闭）。",
        "> 每条请打 1～3 分；不能接受者在「不能接受」列打 ✓ 并写一句原因。",
        "",
        "## 评分说明",
        "",
        "| 维度 | 含义 |",
        "| --- | --- |",
        "| 路径准确 | 是否说清去 App／网银哪里操作 |",
        "| 边界清楚 | 是否说清不能查真账／批额／承诺到账等 |",
        "| 不含糊 | 有无「多半／一般／大概」等 |",
        "| 可执行 | 是否有自助路径或转人工 |",
        "| 合规 | 无收益承诺、不索要卡号／密码／验证码 |",
        "",
        "建议通过线：五维平均 ≥ 2，且无「不能接受」。",
        "",
        "## 样例与打分",
        "",
    ]
    for row in rows:
        chips = "／".join(str(c) for c in (row["chips"] or [])) or "（无）"
        lines.extend(
            [
                f"### {row['id']} · {row['scene']}",
                "",
                f"- 用户：{row['user']}",
                f"- 来源：`{row['source']}` · 模板：`{row['graphic']}`",
                f"- 建议转人工：{'是' if row['suggest_transfer'] else '否'}",
                f"- 选项：{chips}",
                f"- 口播：{row['spoken']}",
                "",
                "| 路径准确 | 边界清楚 | 不含糊 | 可执行 | 合规 | 不能接受 | 备注 |",
                "| --- | --- | --- | --- | --- | --- | --- |",
                "|  |  |  |  |  |  |  |",
                "",
            ]
        )
    lines.extend(
        [
            "## 汇总（打分后由产品经理或助手填写）",
            "",
            "- 平均分：",
            "- 不能接受条数：",
            "- 是否写入 D2 通过线：是／否／暂缓",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    rows = _run()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(_md(rows), encoding="utf-8")
    meta = OUT.with_name("samples.json")
    meta.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"wrote {meta}")


if __name__ == "__main__":
    main()
