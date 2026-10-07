from __future__ import annotations

import json
from typing import Any

from app.services import finance_followup as ff

# 电商售后样例已归档：会话态强制 idle，快捷选项不再下发。
ECOMMERCE_FLOW_KEYS = (
    "return_flow",
    "refund_flow",
    "logistics_flow",
    "invoice_flow",
    "address_flow",
    "cancel_flow",
    "exchange_flow",
    "payment_flow",
    "coupon_flow",
    "warranty_flow",
    "points_flow",
    "price_protect_flow",
    "stock_flow",
)


def _force_idle_ecommerce(state: dict[str, Any]) -> dict[str, Any]:
    out = dict(state)
    for key in ECOMMERCE_FLOW_KEYS:
        out[key] = "idle"
    out["return_reason_category"] = None
    return out


# 以下关键词／退货多轮函数保留供归档测试；现行路由不再调用。

CONFIRM_KEYWORDS = (
    "确认退货",
    "就要退货",
    "一定要退",
    "我要办理退货",
    "退货申请怎么点",
    "怎么提交退货",
    "教我退货操作",
    "还是要退",
)

EXCHANGE_KEYWORDS = ("想换货", "换货", "换一个", "换尺码")
REPLACEMENT_KEYWORDS = ("要补发", "补发", "重新发", "再发一件")
TRANSFER_KEYWORDS = ("转人工", "人工客服", "找人工")

ASK_RETURN_KEYWORDS = ("退货", "怎么退", "退回商品")

REASON_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("size", ("尺码", "大小", "太大", "太小", "不合身")),
    ("wrong_item", ("发错", "错款", "不是我买的", "寄错", "发错货")),
    ("quality", ("质量", "破损", "坏了", "瑕疵", "损坏", "有问题")),
)


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def classify_reason(text: str) -> str:
    for category, kws in REASON_RULES:
        if _contains_any(text, kws):
            return category
    return "other"


def load_state(raw: str | None) -> dict[str, Any]:
    empty = {
        "return_flow": "idle",
        "return_reason_category": None,
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
        "account_seen": "",
        "transfer_flow": "idle",
        "transfer_seen": "",
        "card_flow": "idle",
        "card_seen": "",
        "auth_flow": "idle",
        "auth_seen": "",
        "credit_flow": "idle",
        "credit_seen": "",
        "wealth_flow": "idle",
        "wealth_seen": "",
        "branch_flow": "idle",
        "branch_seen": "",
    }
    if not raw:
        return dict(empty)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return dict(empty)
    if not isinstance(data, dict):
        return dict(empty)
    flow = data.get("return_flow", "idle")
    if flow not in {"idle", "awaiting_reason", "reason_heard"}:
        flow = "idle"
    cat = data.get("return_reason_category")
    if cat not in {"size", "wrong_item", "quality", "other", None}:
        cat = None

    def _clarify(key: str) -> str:
        v = data.get(key, "idle")
        if key == "cancel_flow":
            return v if v in {"idle", "awaiting_clarify", "retaining"} else "idle"
        if key == "credit_flow":
            return v if v in {"idle", "awaiting_clarify", "awaiting_apply"} else "idle"
        return v if v in {"idle", "awaiting_clarify"} else "idle"

    return _force_idle_ecommerce(
        {
            "return_flow": flow,
            "return_reason_category": cat,
            "refund_flow": _clarify("refund_flow"),
            "logistics_flow": _clarify("logistics_flow"),
            "invoice_flow": _clarify("invoice_flow"),
            "address_flow": _clarify("address_flow"),
            "cancel_flow": _clarify("cancel_flow"),
            "exchange_flow": _clarify("exchange_flow"),
            "complaint_flow": _clarify("complaint_flow"),
            "complaint_seen": str(data.get("complaint_seen") or ""),
            "payment_flow": _clarify("payment_flow"),
            "coupon_flow": _clarify("coupon_flow"),
            "warranty_flow": _clarify("warranty_flow"),
            "points_flow": _clarify("points_flow"),
            "price_protect_flow": _clarify("price_protect_flow"),
            "stock_flow": _clarify("stock_flow"),
            "account_flow": _clarify("account_flow"),
            "account_seen": str(data.get("account_seen") or ""),
            "transfer_flow": _clarify("transfer_flow"),
            "transfer_seen": str(data.get("transfer_seen") or ""),
            "card_flow": _clarify("card_flow"),
            "card_seen": str(data.get("card_seen") or ""),
            "auth_flow": _clarify("auth_flow"),
            "auth_seen": str(data.get("auth_seen") or ""),
            "credit_flow": _clarify("credit_flow"),
            "credit_seen": str(data.get("credit_seen") or ""),
            "wealth_flow": _clarify("wealth_flow"),
            "wealth_seen": str(data.get("wealth_seen") or ""),
            "branch_flow": _clarify("branch_flow"),
            "branch_seen": str(data.get("branch_seen") or ""),
        }
    )


def dump_state(state: dict[str, Any]) -> str:
    return json.dumps(
        {
            "return_flow": state.get("return_flow", "idle"),
            "return_reason_category": state.get("return_reason_category"),
            "refund_flow": state.get("refund_flow", "idle"),
            "logistics_flow": state.get("logistics_flow", "idle"),
            "invoice_flow": state.get("invoice_flow", "idle"),
            "address_flow": state.get("address_flow", "idle"),
            "cancel_flow": state.get("cancel_flow", "idle"),
            "exchange_flow": state.get("exchange_flow", "idle"),
            "complaint_flow": state.get("complaint_flow", "idle"),
            "complaint_seen": state.get("complaint_seen") or "",
            "payment_flow": state.get("payment_flow", "idle"),
            "coupon_flow": state.get("coupon_flow", "idle"),
            "warranty_flow": state.get("warranty_flow", "idle"),
            "points_flow": state.get("points_flow", "idle"),
            "price_protect_flow": state.get("price_protect_flow", "idle"),
            "stock_flow": state.get("stock_flow", "idle"),
            "account_flow": state.get("account_flow", "idle"),
            "account_seen": state.get("account_seen") or "",
            "transfer_flow": state.get("transfer_flow", "idle"),
            "transfer_seen": state.get("transfer_seen") or "",
            "card_flow": state.get("card_flow", "idle"),
            "card_seen": state.get("card_seen") or "",
            "auth_flow": state.get("auth_flow", "idle"),
            "auth_seen": state.get("auth_seen") or "",
            "credit_flow": state.get("credit_flow", "idle"),
            "credit_seen": state.get("credit_seen") or "",
            "wealth_flow": state.get("wealth_flow", "idle"),
            "wealth_seen": state.get("wealth_seen") or "",
            "branch_flow": state.get("branch_flow", "idle"),
            "branch_seen": state.get("branch_seen") or "",
        },
        ensure_ascii=False,
    )


def _reply(
    spoken: str,
    graphic: str,
    *,
    action: str = "nod",
    suggest_transfer: bool = False,
) -> dict[str, Any]:
    return {
        "spoken_text": spoken,
        "graphic_template_ref": graphic,
        "action_intent": action,
        "suggest_transfer_human": suggest_transfer,
    }


def process_reply() -> dict[str, Any]:
    return _reply(
        "好，确认要退的话：进订单详情选商品提交退货申请，"
        "按提示填原因、选寄回方式就行。收货核对后会退款。"
        "办的过程中要人工，把订单号发我就行。",
        "faq:return_process",
    )


def ask_reason_reply() -> dict[str, Any]:
    return _reply(
        "理解，您在考虑退货。方便说下是商品有问题、发错货、尺码不对，还是别的？"
        "我先帮您看看有没有更合适的办法；确认要退，再一步步带您办。",
        "faq:return_reason",
    )


def exchange_reply() -> dict[str, Any]:
    return _reply(
        "换货通常比直接退更快：进订单详情找「申请换货」，选好规格提交。"
        "不支持换货的话，可回「确认退货」，或回「转人工」让同事看。",
        "faq:return_exchange",
    )


def replacement_reply() -> dict[str, Any]:
    return _reply(
        "补发多用于发错或漏发：进订单详情找「申请补发／售后」。"
        "找不到入口就带订单号回「转人工」。想直接退也可回「确认退货」。",
        "faq:return_replacement",
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return _reply(
        "行，您点一下「转人工」，同事帮您处理。"
        "转之前如果还想自助退货，也可先回「确认退货」。",
        "faq:return_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def heard_reason_reply(user_text: str, category: str) -> dict[str, Any]:
    snippet = (user_text or "").strip()
    if len(snippet) > 40:
        snippet = snippet[:40] + "…"
    lead = f"收到，您说的是「{snippet}」。" if snippet else "收到，谢谢说明。"

    if category == "size":
        body = (
            f"{lead}尺码不对时，很多单其实能换，不一定非退。"
            "可回「想换货」听指引；还是要退就回「确认退货」；要同事就回「转人工」。"
        )
        graphic = "faq:return_reason_size"
    elif category == "wrong_item":
        body = (
            f"{lead}发错货的话，常见是补发对的，或直接退。"
            "可回「要补发」；想退就回「确认退货」；要核对就回「转人工」。"
        )
        graphic = "faq:return_reason_wrong_item"
    elif category == "quality":
        body = (
            f"{lead}质量或破损我先记下了。"
            "最好先拍个照；要退回「确认退货」，要优先处理回「转人工」。"
        )
        graphic = "faq:return_reason_quality"
    else:
        body = (
            f"{lead}我先记下。也可以看看换货、补发或找客服，不一定马上退。"
            "要退回「确认退货」；想换货回「想换货」；要补发回「要补发」；要同事回「转人工」。"
        )
        graphic = "faq:return_reason_heard"

    return _reply(body, graphic)


def _chip(label: str, text: str | None = None) -> dict[str, str]:
    return {"label": label, "text": text or label}


def quick_replies_for_state(state: dict[str, Any]) -> list[dict[str, str]]:
    """仅按零售金融多轮状态给出可点选项；电商态已强制 idle。"""
    if state.get("complaint_flow") == "awaiting_clarify":
        return ff.topic_chips(
            ("account", "card", "service"),
            {"account": "账户交易纠纷", "card": "卡片额度相关", "service": "服务态度"},
            state.get("complaint_seen"),
        )
    if state.get("branch_flow") == "awaiting_clarify":
        return ff.topic_chips(
            ("find", "hours", "cs"),
            {"find": "怎么查网点", "hours": "网点营业时间", "cs": "客服在线时间"},
            state.get("branch_seen"),
        )
    if state.get("wealth_flow") == "awaiting_clarify":
        return ff.topic_chips(
            ("doc", "risk", "yield"),
            {"doc": "在哪看说明书", "risk": "风险等级怎么看", "yield": "收益怎么理解"},
            state.get("wealth_seen"),
        )
    if state.get("credit_flow") == "awaiting_apply":
        return ff.topic_chips(
            ("pick", "docs", "steps"),
            {"pick": "卡种怎么选", "docs": "申请材料", "steps": "申请步骤"},
            state.get("credit_seen"),
        )
    if state.get("credit_flow") == "awaiting_clarify":
        return ff.topic_chips(
            ("apply", "limit", "repay", "raise"),
            {
                "apply": "办卡申请",
                "limit": "查额度",
                "repay": "还款与账单",
                "raise": "申请提额",
            },
            state.get("credit_seen"),
        )
    if state.get("auth_flow") == "awaiting_clarify":
        return ff.topic_chips(
            ("login", "password", "otp"),
            {"login": "登录不上", "password": "忘记密码", "otp": "收不到验证码"},
            state.get("auth_seen"),
        )
    if state.get("card_flow") == "awaiting_clarify":
        return ff.topic_chips(
            ("bind", "unbind", "loss"),
            {"bind": "怎么绑卡", "unbind": "解绑卡片", "loss": "挂失引导"},
            state.get("card_seen"),
        )
    if state.get("transfer_flow") == "awaiting_clarify":
        return ff.topic_chips(
            ("howto", "fail", "missing", "eta"),
            {
                "howto": "怎么转账",
                "fail": "转账失败",
                "missing": "对方没收到",
                "eta": "多久能到",
            },
            state.get("transfer_seen"),
        )
    if state.get("account_flow") == "awaiting_clarify":
        return ff.topic_chips(
            ("balance", "ledger", "mismatch"),
            {"balance": "查余额", "ledger": "查流水", "mismatch": "余额对不上"},
            state.get("account_seen"),
        )
    return []


def try_return_dialogue(
    text: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """电商退货多轮已下线；始终不接单，并复位电商态。"""
    _ = text
    return None, _force_idle_ecommerce(state)
