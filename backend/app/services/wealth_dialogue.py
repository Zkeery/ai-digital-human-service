from __future__ import annotations

from typing import Any

from app.services import finance_followup as ff
from app.services import return_dialogue as rd

# 理财说明书：短澄清 → 分支答后仍保留选项，追问是否还要咨询其他项

ASK_WEALTH_KEYWORDS = (
    "理财",
    "理财产品",
    "产品说明书",
    "说明书",
    "理财说明书",
    "风险等级",
    "理财收益",
    "看说明书",
    "在哪看说明书",
    "风险等级怎么看",
    "收益怎么理解",
)
DOC_KEYWORDS = ("在哪看说明书", "看说明书", "产品说明书", "说明书入口", "理财说明书")
RISK_KEYWORDS = ("风险等级怎么看", "风险等级", "风险评级", "适合度")
YIELD_KEYWORDS = ("收益怎么理解", "理财收益", "收益率", "预期收益", "承诺收益")
HUMAN_KEYWORDS = ("转人工", "人工客服", "找人工")
DONE_KEYWORDS = ("不用了", "没有了", "先这样", "没了", "就这些", "暂时不用")

TOPIC_LABELS = {
    "doc": "在哪看说明书",
    "risk": "风险等级怎么看",
    "yield": "收益怎么理解",
}
TOPIC_ORDER = ("doc", "risk", "yield")

_BUSY = (
    "account_flow",
    "transfer_flow",
    "card_flow",
    "auth_flow",
    "credit_flow",
    "branch_flow",
    "complaint_flow",
)


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def _parse_seen(raw: Any) -> set[str]:
    if not raw:
        return set()
    if isinstance(raw, list):
        return {str(x) for x in raw if str(x) in TOPIC_LABELS}
    return {p for p in str(raw).split(",") if p in TOPIC_LABELS}


def _dump_seen(seen: set[str]) -> str:
    return ",".join(k for k in TOPIC_ORDER if k in seen)


def _follow_up(seen: set[str]) -> str:
    remain = [TOPIC_LABELS[k] for k in TOPIC_ORDER if k not in seen]
    if not remain:
        return "如还需核对说明书细节，请点「转人工」，或直接说其他问题。"
    parts = [f"「{x}」" for x in remain]
    if len(parts) == 1:
        joined = parts[0]
    elif len(parts) == 2:
        joined = f"{parts[0]}或{parts[1]}"
    else:
        joined = "、".join(parts[:-1]) + f"或{parts[-1]}"
    return f"您还想咨询{joined}吗？可继续点下方选项。"


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "请问您要找说明书入口、了解风险等级怎么看，还是理解收益表述？点下方选项即可。",
        "faq:wealth_clarify",
        action="none",
    )


def done_reply() -> dict[str, Any]:
    return rd._reply(
        "好的。如还有理财说明书相关问题，可随时再问；需要同事协助请点「转人工」。",
        "faq:wealth_done",
        action="none",
        suggest_transfer=True,
    )


def doc_body() -> str:
    return (
        "请打开 App「理财」或「财富」，进入对应产品详情页，"
        "在资料／文件区打开产品说明书或风险揭示书。"
        "若找不到产品页或文件入口，请点「转人工」。"
    )


def risk_body() -> str:
    return (
        "请以产品说明书或风险揭示书中的风险等级披露为准；"
        "本客服不替您判断是否适合购买。"
        "若说明书打不开或等级显示异常，请点「转人工」。"
    )


def yield_body() -> str:
    return (
        "说明书中的历史业绩、测算或业绩比较基准，均不等于对未来收益的承诺。"
        "具体条款以您打开的产品说明书原文为准。"
        "若需要核对某段表述，请点「转人工」。"
    )


def _branch_reply(topic: str, seen: set[str]) -> tuple[dict[str, Any], set[str]]:
    bodies = {"doc": doc_body, "risk": risk_body, "yield": yield_body}
    graphics = {"doc": "faq:wealth_doc", "risk": "faq:wealth_risk", "yield": "faq:wealth_yield"}
    new_seen = set(seen)
    new_seen.add(topic)
    spoken = bodies[topic]() + _follow_up(new_seen)
    return (
        rd._reply(
            spoken,
            graphics[topic],
            action="none",
            suggest_transfer=True,
        ),
        new_seen,
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "好的，请点「转人工」，我帮您接通同事。",
        "faq:wealth_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def try_wealth_dialogue(
    text: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    for key in _BUSY:
        if state.get(key, "idle") != "idle":
            return None, state

    wealth = state.get("wealth_flow", "idle")
    seen = _parse_seen(state.get("wealth_seen"))

    def pack(**kwargs: Any) -> dict[str, Any]:
        base = {
            "return_flow": "idle",
            "return_reason_category": state.get("return_reason_category"),
            "refund_flow": "idle",
            "logistics_flow": "idle",
            "invoice_flow": "idle",
            "address_flow": "idle",
            "cancel_flow": "idle",
            "exchange_flow": "idle",
            "complaint_flow": "idle",
            "complaint_seen": "",
            "payment_flow": "idle",
            "coupon_flow": "idle",
            "warranty_flow": "idle",
            "points_flow": "idle",
            "price_protect_flow": "idle",
            "stock_flow": "idle",
            "account_flow": "idle",
            "transfer_flow": "idle",
            "card_flow": "idle",
            "auth_flow": "idle",
            "credit_flow": "idle",
            "wealth_flow": wealth,
            "wealth_seen": _dump_seen(seen),
            "branch_flow": "idle",
            "branch_seen": "",
        }
        base.update(kwargs)
        if "wealth_seen" in kwargs and isinstance(kwargs["wealth_seen"], set):
            base["wealth_seen"] = _dump_seen(kwargs["wealth_seen"])
        return base

    def answer(topic: str) -> tuple[dict[str, Any], dict[str, Any]]:
        reply, new_seen = _branch_reply(topic, seen)
        # stay in clarify so chips remain; clear seen only on human/done
        if len(new_seen) >= len(TOPIC_ORDER):
            return reply, pack(wealth_flow="idle", wealth_seen="")
        return reply, pack(wealth_flow="awaiting_clarify", wealth_seen=new_seen)

    if wealth == "awaiting_clarify":
        if _contains_any(text, HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(wealth_flow="idle", wealth_seen="")
        if _contains_any(text, DONE_KEYWORDS):
            return done_reply(), pack(wealth_flow="idle", wealth_seen="")
        if _contains_any(text, YIELD_KEYWORDS):
            return answer("yield")
        if _contains_any(text, RISK_KEYWORDS):
            return answer("risk")
        if _contains_any(text, DOC_KEYWORDS):
            return answer("doc")
        if ff.should_keep_clarify_lock(text):
            return clarify_reply(), pack(wealth_flow="awaiting_clarify", wealth_seen=seen)
        # 未命中本场景：释放澄清态，避免换话题仍被同一句锁死
        return None, pack(wealth_flow="idle", wealth_seen="")

    if _contains_any(text, ASK_WEALTH_KEYWORDS):
        if _contains_any(text, HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(wealth_flow="idle", wealth_seen="")
        if _contains_any(text, YIELD_KEYWORDS):
            return answer("yield")
        if _contains_any(text, RISK_KEYWORDS):
            return answer("risk")
        if _contains_any(text, DOC_KEYWORDS):
            return answer("doc")
        return clarify_reply(), pack(wealth_flow="awaiting_clarify", wealth_seen="")

    return None, state
