from __future__ import annotations

from typing import Any

from app.services import finance_followup as ff
from app.services import return_dialogue as rd

# 银行卡：短澄清 → 分支答后保留选项并追问（不代办挂失）

ASK_CARD_KEYWORDS = (
    "银行卡",
    "借记卡",
    "卡号",
    "绑卡",
    "绑定银行卡",
    "解绑",
    "解绑卡",
    "挂失",
    "卡片挂失",
    "卡丢了",
    "卡被盗",
    "怎么绑卡",
    "怎么绑",
    "解绑卡片",
    "挂失引导",
)
BIND_KEYWORDS = ("怎么绑卡", "怎么绑", "绑卡", "绑定银行卡", "加卡", "添加银行卡")
UNBIND_KEYWORDS = ("解绑卡片", "解绑卡", "解绑", "取消绑定")
LOSS_KEYWORDS = ("挂失引导", "挂失", "卡片挂失", "卡丢了", "卡被盗", "报失")

TOPIC_LABELS = {
    "bind": "怎么绑卡",
    "unbind": "解绑卡片",
    "loss": "挂失引导",
}
TOPIC_ORDER = ("bind", "unbind", "loss")

_BUSY = (
    "account_flow",
    "transfer_flow",
    "auth_flow",
    "credit_flow",
    "wealth_flow",
    "branch_flow",
    "complaint_flow",
)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "请问您要绑卡、解绑，还是挂失？请点下方选项。",
        "faq:card_clarify",
        action="none",
    )


def done_reply() -> dict[str, Any]:
    return rd._reply(
        "好的。如还有银行卡问题，可随时再问；需要同事协助请点「转人工」。",
        "faq:card_done",
        action="none",
        suggest_transfer=True,
    )


def bind_body() -> str:
    return (
        "请打开 App，进入「我的」→「银行卡」或「账户管理」，选择添加／绑定银行卡，按页面完成验证。"
        "若无入口或验证失败，请点「转人工」。"
    )


def unbind_body() -> str:
    return (
        "请打开 App「银行卡」或「账户管理」，选中对应卡片后选择解绑／解除绑定。"
        "若无法解绑或解绑后仍有扣款，请点「转人工」。"
    )


def loss_body() -> str:
    return (
        "卡片遗失或被盗时，请立即通过 App／网银的官方挂失功能办理，或点「转人工」。"
        "本客服不能代办挂失；请勿发送完整卡号。"
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "好的，请点「转人工」，我帮您接通同事。",
        "faq:card_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def _topic_reply(topic: str, seen: set[str]) -> tuple[dict[str, Any], set[str]]:
    bodies = {"bind": bind_body, "unbind": unbind_body, "loss": loss_body}
    graphics = {
        "bind": "faq:card_bind",
        "unbind": "faq:card_unbind",
        "loss": "faq:card_loss",
    }
    new_seen = set(seen)
    new_seen.add(topic)
    spoken = bodies[topic]() + ff.follow_up(
        new_seen,
        TOPIC_LABELS,
        TOPIC_ORDER,
        closing="如还需办理卡片事项，请点「转人工」，或直接说其他问题。",
    )
    return (
        rd._reply(spoken, graphics[topic], action="none", suggest_transfer=True),
        new_seen,
    )


def try_card_dialogue(
    text: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    for key in _BUSY:
        if state.get(key, "idle") != "idle":
            return None, state

    card = state.get("card_flow", "idle")
    seen = ff.parse_seen(state.get("card_seen"), TOPIC_LABELS)

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
            "account_seen": "",
            "transfer_flow": "idle",
            "transfer_seen": "",
            "card_flow": card,
            "card_seen": ff.dump_seen(seen, TOPIC_ORDER),
            "auth_flow": "idle",
            "auth_seen": "",
            "credit_flow": "idle",
            "credit_seen": "",
            "wealth_flow": "idle",
            "wealth_seen": "",
            "branch_flow": "idle",
            "branch_seen": "",
        }
        base.update(kwargs)
        if "card_seen" in kwargs and isinstance(kwargs["card_seen"], set):
            base["card_seen"] = ff.dump_seen(kwargs["card_seen"], TOPIC_ORDER)
        return base

    def answer(topic: str) -> tuple[dict[str, Any], dict[str, Any]]:
        reply, new_seen = _topic_reply(topic, seen)
        if len(new_seen) >= len(TOPIC_ORDER):
            return reply, pack(card_flow="idle", card_seen="")
        return reply, pack(card_flow="awaiting_clarify", card_seen=new_seen)

    if card == "awaiting_clarify":
        if ff.contains_any(text, ff.HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(card_flow="idle", card_seen="")
        if ff.contains_any(text, ff.DONE_KEYWORDS):
            return done_reply(), pack(card_flow="idle", card_seen="")
        if ff.contains_any(text, LOSS_KEYWORDS):
            return answer("loss")
        if ff.contains_any(text, UNBIND_KEYWORDS):
            return answer("unbind")
        if ff.contains_any(text, BIND_KEYWORDS):
            return answer("bind")
        if ff.should_keep_clarify_lock(text):
            return clarify_reply(), pack(card_flow="awaiting_clarify", card_seen=seen)
        # 未命中本场景：释放澄清态，避免换话题仍被同一句锁死
        return None, pack(card_flow="idle", card_seen="")

    if ff.contains_any(text, ASK_CARD_KEYWORDS):
        if ff.contains_any(text, ff.HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(card_flow="idle", card_seen="")
        if ff.contains_any(text, LOSS_KEYWORDS):
            return answer("loss")
        if ff.contains_any(text, UNBIND_KEYWORDS):
            return answer("unbind")
        if ff.contains_any(text, BIND_KEYWORDS):
            return answer("bind")
        return clarify_reply(), pack(card_flow="awaiting_clarify", card_seen="")

    return None, state
