"""金融话术：禁止含糊措辞（准确度门禁）。"""

from __future__ import annotations

import ast
from pathlib import Path

SERVICES = Path(__file__).resolve().parents[1] / "app" / "services"
FINANCE_MODULES = (
    "account_dialogue.py",
    "transfer_dialogue.py",
    "card_dialogue.py",
    "auth_dialogue.py",
    "credit_dialogue.py",
    "wealth_dialogue.py",
    "branch_dialogue.py",
    "complaint_dialogue.py",
)
BANNED = ("多半", "一般", "大概", "或许", "可能", "吃不准", "保证不了", "没法保证")


def _string_literals(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(node.value)
    return out


def test_finance_spoken_has_no_vague_words():
    hits: list[str] = []
    for name in FINANCE_MODULES:
        path = SERVICES / name
        for s in _string_literals(path):
            for bad in BANNED:
                if bad in s:
                    hits.append(f"{name}: contains「{bad}」in {s[:40]}…")
    assert not hits, "金融话术含糊措辞：\n" + "\n".join(hits)
