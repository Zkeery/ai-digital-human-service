from __future__ import annotations

from typing import Any

from app.services import return_dialogue as rd

# 缺货／到货通知：短澄清 → 什么时候有货／订到货通知／订了没通知／转人工

ASK_STOCK_KEYWORDS = (
    "到货通知",
    "什么时候有货",
    "缺货",
    "没货",
    "无货",
    "补货",
    "有货了吗",
)
WHEN_KEYWORDS = ("什么时候有货", "何时有货", "啥时候有", "预计到货", "什么时候补")
SUBSCRIBE_KEYWORDS = ("订到货通知", "到货提醒", "订阅到货", "怎么订通知", "设个提醒")
MISSED_KEYWORDS = ("订了没通知", "没收到通知", "通知没来", "订了也没信")
TRANSFER_KEYWORDS = ("转人工", "人工客服", "找人工")


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "缺货这边想问啥？点一下，或直接说就行。",
        "faq:stock_clarify",
        action="none",
    )


def when_reply() -> dict[str, Any]:
    return rd._reply(
        "商品页或购物车里，缺货时有时会写预计到货。"
        "看不到的话，把商品名或链接发我，点「转人工」帮您问。",
        "faq:stock_when",
        action="none",
        suggest_transfer=True,
    )


def subscribe_reply() -> dict[str, Any]:
    return rd._reply(
        "缺货商品页一般有「到货通知／到货提醒」，点一下留手机或账号就行。"
        "没有入口就点「转人工」帮您看。",
        "faq:stock_subscribe",
        action="none",
        suggest_transfer=True,
    )


def missed_reply() -> dict[str, Any]:
    return rd._reply(
        "先截一下当时订通知的页面或短信。"
        "把商品名和时间发我，点「转人工」帮您核对。",
        "faq:stock_missed",
        action="none",
        suggest_transfer=True,
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "行，您点一下「转人工」，我帮您叫同事。",
        "faq:stock_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def try_stock_dialogue(
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
        "price_protect_flow",
    )
    for key in busy:
        if state.get(key, "idle") != "idle":
            return None, state

    stock = state.get("stock_flow", "idle")
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
            "price_protect_flow": "idle",
            "stock_flow": stock,
        }
        base.update(kwargs)
        return base

    if stock == "awaiting_clarify":
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(stock_flow="idle")
        if _contains_any(text, MISSED_KEYWORDS):
            return missed_reply(), pack(stock_flow="idle")
        if _contains_any(text, SUBSCRIBE_KEYWORDS):
            return subscribe_reply(), pack(stock_flow="idle")
        if _contains_any(text, WHEN_KEYWORDS):
            return when_reply(), pack(stock_flow="idle")
        return clarify_reply(), pack(stock_flow="awaiting_clarify")

    if _contains_any(text, ASK_STOCK_KEYWORDS):
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(stock_flow="idle")
        if _contains_any(text, MISSED_KEYWORDS):
            return missed_reply(), pack(stock_flow="idle")
        if _contains_any(text, SUBSCRIBE_KEYWORDS):
            return subscribe_reply(), pack(stock_flow="idle")
        if _contains_any(text, WHEN_KEYWORDS) and not _contains_any(
            text, ("到货通知",)
        ):
            # 「什么时候有货」可直接答；单独「到货通知」走澄清
            return when_reply(), pack(stock_flow="idle")
        return clarify_reply(), pack(stock_flow="awaiting_clarify")

    return None, state
