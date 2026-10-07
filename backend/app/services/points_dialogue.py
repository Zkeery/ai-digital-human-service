from __future__ import annotations

from typing import Any

from app.services import return_dialogue as rd

# 会员／积分：短澄清 → 查积分／怎么用／积分不对／转人工

ASK_POINTS_KEYWORDS = ("会员积分", "积分问题", "我的积分", "会员权益", "积分", "会员")
BALANCE_KEYWORDS = ("查积分", "积分多少", "看积分", "积分余额", "还有多少分")
USE_KEYWORDS = ("怎么用", "怎么抵扣", "积分兑换", "抵现", "怎么花积分")
WRONG_KEYWORDS = ("积分不对", "少了积分", "积分没到", "积分错了", "少积分")
TRANSFER_KEYWORDS = ("转人工", "人工客服", "找人工")


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "积分这边想问啥？点一下，或直接说就行。",
        "faq:points_clarify",
        action="none",
    )


def balance_reply() -> dict[str, Any]:
    return rd._reply(
        "去「我的－会员／积分」就能看余额。看不到或显示不对，点「转人工」帮您查。",
        "faq:points_balance",
        action="none",
        suggest_transfer=True,
    )


def use_reply() -> dict[str, Any]:
    return rd._reply(
        "结算时一般能勾积分抵扣，也能去积分商城换。找不到入口就点「转人工」，问下现在怎么用。",
        "faq:points_use",
        action="none",
        suggest_transfer=True,
    )


def wrong_reply() -> dict[str, Any]:
    return rd._reply(
        "先截个积分明细或订单页，带上大概时间和订单号，点「转人工」帮您核对。",
        "faq:points_wrong",
        action="none",
        suggest_transfer=True,
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "行，您点一下「转人工」，我帮您叫同事。",
        "faq:points_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def try_points_dialogue(
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
        "price_protect_flow",
        "stock_flow",
    )
    for key in busy:
        if state.get(key, "idle") != "idle":
            return None, state

    points = state.get("points_flow", "idle")
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
            "points_flow": points,
            "price_protect_flow": "idle",
            "stock_flow": "idle",
        }
        base.update(kwargs)
        return base

    if points == "awaiting_clarify":
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(points_flow="idle")
        if _contains_any(text, BALANCE_KEYWORDS):
            return balance_reply(), pack(points_flow="idle")
        if _contains_any(text, USE_KEYWORDS):
            return use_reply(), pack(points_flow="idle")
        if _contains_any(text, WRONG_KEYWORDS):
            return wrong_reply(), pack(points_flow="idle")
        return clarify_reply(), pack(points_flow="awaiting_clarify")

    if _contains_any(text, ASK_POINTS_KEYWORDS):
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(points_flow="idle")
        if _contains_any(text, BALANCE_KEYWORDS):
            return balance_reply(), pack(points_flow="idle")
        if _contains_any(text, USE_KEYWORDS):
            return use_reply(), pack(points_flow="idle")
        if _contains_any(text, WRONG_KEYWORDS):
            return wrong_reply(), pack(points_flow="idle")
        return clarify_reply(), pack(points_flow="awaiting_clarify")

    return None, state
