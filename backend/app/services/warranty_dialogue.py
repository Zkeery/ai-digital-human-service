from __future__ import annotations

from typing import Any

from app.services import return_dialogue as rd

# 保修／质保：短澄清 → 在不在保／怎么申请／保修进度／转人工

ASK_WARRANTY_KEYWORDS = ("保修问题", "质保问题", "保修", "质保", "保修期", "三包")
COVERAGE_KEYWORDS = ("在不在保", "还在保吗", "过保了吗", "保修期多久", "还保吗")
APPLY_KEYWORDS = ("怎么申请", "如何保修", "申请保修", "去哪保修", "寄修")
PROGRESS_KEYWORDS = ("保修进度", "修到哪了", "寄修进度", "维修进度")
TRANSFER_KEYWORDS = ("转人工", "人工客服", "找人工")


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "保修这边想问哪块？点一下，或直接说就行。",
        "faq:warranty_clarify",
        action="none",
    )


def coverage_reply() -> dict[str, Any]:
    return rd._reply(
        "订单详情或商品页里，通常能看到保修说明。看不清就把订单号发我，点「转人工」。",
        "faq:warranty_coverage",
        action="none",
        suggest_transfer=True,
    )


def apply_reply() -> dict[str, Any]:
    return rd._reply(
        "进订单详情找「申请售后／保修」，跟着页面走就行。没有入口或提交失败，点「转人工」帮您办。",
        "faq:warranty_apply",
        action="none",
        suggest_transfer=True,
    )


def progress_reply() -> dict[str, Any]:
    return rd._reply(
        "提交过的保修，多半在订单售后进度里。找不到或一直没动静，把售后单号发我并点「转人工」。",
        "faq:warranty_progress",
        action="none",
        suggest_transfer=True,
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "行，您点一下「转人工」，我帮您叫同事。",
        "faq:warranty_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def try_warranty_dialogue(
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
        "points_flow",
        "price_protect_flow",
        "stock_flow",
    )
    for key in busy:
        if state.get(key, "idle") != "idle":
            return None, state

    warranty = state.get("warranty_flow", "idle")
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
            "warranty_flow": warranty,
            "points_flow": "idle",
            "price_protect_flow": "idle",
            "stock_flow": "idle",
        }
        base.update(kwargs)
        return base

    if warranty == "awaiting_clarify":
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(warranty_flow="idle")
        if _contains_any(text, COVERAGE_KEYWORDS):
            return coverage_reply(), pack(warranty_flow="idle")
        if _contains_any(text, APPLY_KEYWORDS):
            return apply_reply(), pack(warranty_flow="idle")
        if _contains_any(text, PROGRESS_KEYWORDS):
            return progress_reply(), pack(warranty_flow="idle")
        return clarify_reply(), pack(warranty_flow="awaiting_clarify")

    if _contains_any(text, ASK_WARRANTY_KEYWORDS):
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(warranty_flow="idle")
        if _contains_any(text, COVERAGE_KEYWORDS):
            return coverage_reply(), pack(warranty_flow="idle")
        if _contains_any(text, APPLY_KEYWORDS):
            return apply_reply(), pack(warranty_flow="idle")
        if _contains_any(text, PROGRESS_KEYWORDS):
            return progress_reply(), pack(warranty_flow="idle")
        return clarify_reply(), pack(warranty_flow="awaiting_clarify")

    return None, state
