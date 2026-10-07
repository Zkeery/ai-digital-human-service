from __future__ import annotations

from typing import Any

from app.services import return_dialogue as rd

# 价保／保价：短澄清 → 怎么申请／适用条件／差价没到／转人工

ASK_PRICE_PROTECT_KEYWORDS = (
    "价格保护",
    "降价补差",
    "申请价保",
    "价保",
    "保价",
)
APPLY_KEYWORDS = ("怎么申请", "怎么价保", "申请价保", "去哪价保", "怎么保价")
RULES_KEYWORDS = ("适用条件", "几天内能保", "能保吗", "价保条件", "多久能保")
PENDING_KEYWORDS = ("差价没到", "价保进度", "补差没到", "没退差价", "差价未到")
TRANSFER_KEYWORDS = ("转人工", "人工客服", "找人工")


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "价保这边想办哪件？点一下，或直接说就行。",
        "faq:price_protect_clarify",
        action="none",
    )


def apply_reply() -> dict[str, Any]:
    return rd._reply(
        "进订单详情找「价保」，跟着页面提交就行。没有入口或点不动，点「转人工」帮您办。",
        "faq:price_protect_apply",
        action="none",
        suggest_transfer=True,
    )


def rules_reply() -> dict[str, Any]:
    return rd._reply(
        "多半要在时限里，且同款同规格才行。吃不准的话发我订单号，点「转人工」。",
        "faq:price_protect_rules",
        action="none",
        suggest_transfer=True,
    )


def pending_reply() -> dict[str, Any]:
    return rd._reply(
        "先截个申请页或到账记录，连订单号一起，点「转人工」帮您查差价。",
        "faq:price_protect_pending",
        action="none",
        suggest_transfer=True,
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "行，您点一下「转人工」，我帮您叫同事。",
        "faq:price_protect_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def try_price_protect_dialogue(
    text: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    busy = (
        "return_flow",
        "refund_flow",
        "logistics_flow",
        "invoice_flow",
        "address_flow",
        "cancel_flow",
        "exchange_flow",
        "complaint_flow",
        "payment_flow",
        "coupon_flow",
        "warranty_flow",
        "points_flow",
        "stock_flow",
    )
    for key in busy:
        if state.get(key, "idle") != "idle":
            return None, state

    price_protect = state.get("price_protect_flow", "idle")
    category = state.get("return_reason_category")

    def pack(**kwargs: Any) -> dict[str, Any]:
        base = {
            "return_flow": "idle",
            "return_reason_category": category,
            "refund_flow": "idle",
            "logistics_flow": "idle",
            "invoice_flow": "idle",
            "address_flow": "idle",
            "cancel_flow": "idle",
            "exchange_flow": "idle",
            "complaint_flow": "idle",
            "payment_flow": "idle",
            "coupon_flow": "idle",
            "warranty_flow": "idle",
            "points_flow": "idle",
            "price_protect_flow": price_protect,
            "stock_flow": "idle",
        }
        base.update(kwargs)
        return base

    if price_protect == "awaiting_clarify":
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(price_protect_flow="idle")
        if _contains_any(text, APPLY_KEYWORDS):
            return apply_reply(), pack(price_protect_flow="idle")
        if _contains_any(text, RULES_KEYWORDS):
            return rules_reply(), pack(price_protect_flow="idle")
        if _contains_any(text, PENDING_KEYWORDS):
            return pending_reply(), pack(price_protect_flow="idle")
        return clarify_reply(), pack(price_protect_flow="awaiting_clarify")

    if _contains_any(text, ASK_PRICE_PROTECT_KEYWORDS):
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(price_protect_flow="idle")
        if _contains_any(text, APPLY_KEYWORDS):
            return apply_reply(), pack(price_protect_flow="idle")
        if _contains_any(text, RULES_KEYWORDS):
            return rules_reply(), pack(price_protect_flow="idle")
        if _contains_any(text, PENDING_KEYWORDS):
            return pending_reply(), pack(price_protect_flow="idle")
        return clarify_reply(), pack(price_protect_flow="awaiting_clarify")

    return None, state
