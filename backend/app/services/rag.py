"""近程 C1／E1～E7：本地样例词法检索（可关／可超时；无 Embedding 外呼）。"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

_CHUNKS_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "pilot_chunks.json"

# 与网点／理财／信用卡／账户／转账／银行卡／登录／投诉主题相关时才尝试 RAG，避免闲聊刷事件
_TOPIC_HINTS = (
    "网点",
    "营业厅",
    "营业时间",
    "开门",
    "客服时间",
    "在线客服",
    "理财",
    "说明书",
    "风险等级",
    "收益",
    "财富",
    "信用卡",
    "办信用卡",
    "查额度",
    "额度",
    "还款日",
    "还款",
    "办卡材料",
    "申请材料",
    "提额",
    "查余额",
    "账户余额",
    "余额查询",
    "查流水",
    "交易明细",
    "账单明细",
    "余额对不上",
    "流水不对",
    "怎么转账",
    "如何转账",
    "我想转账",
    "我要转账",
    "转账失败",
    "转账不了",
    "没到账",
    "未到账",
    "对方没收到",
    "多久能到",
    "多久到账",
    "转账流程",
    "怎么绑卡",
    "绑卡",
    "绑定银行卡",
    "解绑卡片",
    "解绑卡",
    "挂失",
    "卡片挂失",
    "卡丢了",
    "卡被盗",
    "登录不上",
    "登陆不上",
    "登不上",
    "登录失败",
    "登陆失败",
    "进不去",
    "忘记密码",
    "找回密码",
    "重置密码",
    "改密码",
    "收不到验证码",
    "验证码没来",
    "验证码收不到",
    "投诉",
    "纠纷",
    "申诉",
    "举报",
    "乱扣款",
    "莫名扣款",
    "账户交易纠纷",
    "账户纠纷",
    "交易纠纷",
    "服务态度",
    "态度差",
    "客服态度",
    "信用卡纠纷",
    "卡片纠纷",
)

_ANSWER_GRAPHICS = {
    "faq:branch_find",
    "faq:branch_hours",
    "faq:branch_cs",
    "faq:wealth_doc",
    "faq:wealth_risk",
    "faq:wealth_yield",
    "faq:credit_limit",
    "faq:credit_repay",
    "faq:credit_raise",
    "faq:credit_apply_pick",
    "faq:credit_apply_docs",
    "faq:credit_apply_steps",
    "faq:account_balance",
    "faq:account_ledger",
    "faq:account_mismatch",
    "faq:transfer_howto",
    "faq:transfer_fail",
    "faq:transfer_missing",
    "faq:transfer_eta",
    "faq:card_bind",
    "faq:card_unbind",
    "faq:card_loss",
    "faq:auth_login",
    "faq:auth_password",
    "faq:auth_otp",
    "faq:complaint_account",
    "faq:complaint_card",
    "faq:complaint_service",
}


@dataclass
class RetrieveOutcome:
    status: str  # hit | miss | timeout | disabled
    chunk: dict[str, Any] | None = None
    elapsed_ms: int = 0


def topic_eligible(text: str) -> bool:
    t = (text or "").strip().lower()
    return any(h.lower() in t for h in _TOPIC_HINTS)


@lru_cache(maxsize=1)
def load_chunks() -> tuple[dict[str, Any], ...]:
    raw = json.loads(_CHUNKS_PATH.read_text(encoding="utf-8"))
    return tuple(raw)


def _tokens(text: str) -> set[str]:
    # 中文按连续字串切开；英文数字保留
    parts = re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z0-9_]{2,}", (text or "").lower())
    chars = set()
    for p in parts:
        if re.fullmatch(r"[\u4e00-\u9fff]+", p) and len(p) >= 2:
            # 双字窗，提高「营业时间」类命中
            for i in range(len(p) - 1):
                chars.add(p[i : i + 2])
        chars.add(p)
    return chars


def score_chunk(query: str, chunk: dict[str, Any]) -> float:
    q = (query or "").strip().lower()
    if not q:
        return 0.0
    score = 0.0
    for kw in chunk.get("keywords") or []:
        k = str(kw).lower()
        if k and k in q:
            score += 3.0
    q_tokens = _tokens(q)
    c_tokens = _tokens(f"{chunk.get('title', '')} {chunk.get('text', '')}")
    if q_tokens and c_tokens:
        score += 1.5 * len(q_tokens & c_tokens)
    return score


def retrieve(query: str, timeout_seconds: float) -> RetrieveOutcome:
    started = time.perf_counter()
    best: dict[str, Any] | None = None
    best_score = 0.0
    for chunk in load_chunks():
        elapsed = time.perf_counter() - started
        if elapsed >= timeout_seconds:
            return RetrieveOutcome(
                status="timeout",
                elapsed_ms=int(elapsed * 1000),
            )
        s = score_chunk(query, chunk)
        if s > best_score:
            best_score = s
            best = chunk
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    # 至少命中一个关键词级信号
    if best is None or best_score < 3.0:
        return RetrieveOutcome(status="miss", elapsed_ms=elapsed_ms)
    return RetrieveOutcome(status="hit", chunk=dict(best), elapsed_ms=elapsed_ms)


def citation_suffix(chunk: dict[str, Any]) -> str:
    title = str(chunk.get("title") or "样例依据").strip()
    body = str(chunk.get("text") or "").strip()
    return f"\n\n【样例依据·{title}】{body}"


def reply_from_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    body = str(chunk.get("text") or "").strip()
    return {
        "spoken_text": (
            f"{body} 以上为公开演示样例，请以您 App／网点现场披露为准；"
            "需要同事协助请点「转人工」。"
        ),
        "graphic_template_ref": f"rag:{chunk.get('id', 'chunk')}",
        "action_intent": "none",
        "suggest_transfer_human": True,
    }


def apply_to_reply(
    *,
    enabled: bool,
    query: str,
    spoken: str,
    graphic_template_ref: str,
    source: str,
    timeout_seconds: float,
) -> tuple[str, str, str, RetrieveOutcome]:
    """返回 (spoken, source, graphic, outcome)。"""
    if not enabled:
        return spoken, source, graphic_template_ref, RetrieveOutcome(status="disabled")

    if not topic_eligible(query):
        return spoken, source, graphic_template_ref, RetrieveOutcome(status="miss")

    outcome = retrieve(query, timeout_seconds)
    if outcome.status != "hit" or not outcome.chunk:
        return spoken, source, graphic_template_ref, outcome

    chunk = outcome.chunk
    if graphic_template_ref in _ANSWER_GRAPHICS:
        spoken = f"{spoken.rstrip()}{citation_suffix(chunk)}"
        source = f"{source}+rag" if source else "rag"
        return spoken, source, graphic_template_ref, outcome

    # 规则未给出实质网点／理财／信用卡／账户／转账／银行卡答时，允许用样例直接回答
    if source in {"fallback_rule"} or graphic_template_ref.startswith("faq:fallback"):
        built = reply_from_chunk(chunk)
        return (
            built["spoken_text"],
            "rag",
            built["graphic_template_ref"],
            outcome,
        )

    return spoken, source, graphic_template_ref, outcome
