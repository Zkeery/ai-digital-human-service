from __future__ import annotations

from typing import Any

from app.services import return_dialogue as rd

# 优惠券：短澄清 → 用不了／找不到／过期失效／转人工

ASK_COUPON_KEYWORDS = ("优惠券问题", "优惠券", "用券", "折扣码", "红包券", "代金券")
UNUSABLE_KEYWORDS = ("用不了", "用不了券", "无法使用", "不能用", "抵扣不了")
MISSING_KEYWORDS = ("找不到券", "找不到", "没看到券", "券呢", "没有券")
EXPIRED_KEYWORDS = ("过期或失效", "过期", "失效", "作废")
TRANSFER_KEYWORDS = ("转人工", "人工客服", "找人工")


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "优惠券怎么了？点一下，或直接说就行。",
        "faq:coupon_clarify",
        action="none",
    )


def unusable_reply() -> dict[str, Any]:
    return rd._reply(
        "先看券有没有满减门槛、是不是限指定商品。还不行就把订单或商品名发我，点「转人工」。",
        "faq:coupon_unusable",
        action="none",
        suggest_transfer=True,
    )


def missing_reply() -> dict[str, Any]:
    return rd._reply(
        "去「我的－优惠券」瞅一眼有没有。没有的话可能还没到账，或活动结束了；要核对就点「转人工」。",
        "faq:coupon_missing",
        action="none",
        suggest_transfer=True,
    )


def expired_reply() -> dict[str, Any]:
    return rd._reply(
        "过期或失效的券通常用不了。刚过期想核对的话，把券名发我并点「转人工」。",
        "faq:coupon_expired",
        action="none",
        suggest_transfer=True,
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "行，您点一下「转人工」，我帮您叫同事。",
        "faq:coupon_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def try_coupon_dialogue(
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
        "warranty_flow",
        "points_flow",
        "price_protect_flow",
        "stock_flow",
    )
    for key in busy:
        if state.get(key, "idle") != "idle":
            return None, state

    coupon = state.get("coupon_flow", "idle")
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
            "coupon_flow": coupon,
            "warranty_flow": "idle",
            "points_flow": "idle",
            "price_protect_flow": "idle",
            "stock_flow": "idle",
        }
        base.update(kwargs)
        return base

    if coupon == "awaiting_clarify":
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(coupon_flow="idle")
        if _contains_any(text, UNUSABLE_KEYWORDS):
            return unusable_reply(), pack(coupon_flow="idle")
        if _contains_any(text, MISSING_KEYWORDS):
            return missing_reply(), pack(coupon_flow="idle")
        if _contains_any(text, EXPIRED_KEYWORDS):
            return expired_reply(), pack(coupon_flow="idle")
        return clarify_reply(), pack(coupon_flow="awaiting_clarify")

    if _contains_any(text, ASK_COUPON_KEYWORDS):
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(coupon_flow="idle")
        if _contains_any(text, UNUSABLE_KEYWORDS):
            return unusable_reply(), pack(coupon_flow="idle")
        if _contains_any(text, MISSING_KEYWORDS):
            return missing_reply(), pack(coupon_flow="idle")
        if _contains_any(text, EXPIRED_KEYWORDS):
            return expired_reply(), pack(coupon_flow="idle")
        return clarify_reply(), pack(coupon_flow="awaiting_clarify")

    return None, state
