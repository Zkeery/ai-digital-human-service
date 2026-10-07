from __future__ import annotations

from typing import Any

from app.services import finance_followup as ff
from app.services import return_dialogue as rd

# 网点／营业时间：短澄清 → 分支答后保留选项并追问

ASK_BRANCH_KEYWORDS = (
    "网点",
    "营业厅",
    "营业时间",
    "几点开门",
    "开门时间",
    "网点时间",
    "网点查询",
    "附近网点",
    "客服时间",
    "在线客服时间",
    "怎么查网点",
    "网点营业时间",
    "客服在线时间",
)
FIND_KEYWORDS = (
    "怎么查网点",
    "网点查询",
    "附近网点",
    "找网点",
    "查网点",
    "网点在哪",
    "网点哪里",
    "哪里有网点",
    "附近哪里有网点",
    "网点地址",
)
HOURS_KEYWORDS = ("网点营业时间", "营业时间", "几点开门", "开门时间", "网点时间")
CS_HOURS_KEYWORDS = ("客服在线时间", "客服时间", "在线客服时间", "人工客服时间")
HUMAN_KEYWORDS = ("转人工", "人工客服", "找人工")
DONE_KEYWORDS = ("不用了", "没有了", "先这样", "没了", "就这些", "暂时不用")

TOPIC_LABELS = {
    "find": "怎么查网点",
    "hours": "网点营业时间",
    "cs": "客服在线时间",
}
TOPIC_ORDER = ("find", "hours", "cs")

_BUSY = (
    "account_flow",
    "transfer_flow",
    "card_flow",
    "auth_flow",
    "credit_flow",
    "wealth_flow",
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
        return "如还需核对网点信息，请点「转人工」，或直接说其他问题。"
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
        "请问您要查附近网点、看网点营业时间，还是客服在线时间？点下方选项即可。",
        "faq:branch_clarify",
        action="none",
    )


def done_reply() -> dict[str, Any]:
    return rd._reply(
        "好的。如还有网点或营业时间问题，可随时再问；需要同事协助请点「转人工」。",
        "faq:branch_done",
        action="none",
        suggest_transfer=True,
    )


def find_body() -> str:
    return (
        "请打开 App，进入「网点查询」或「附近网点」，"
        "可按定位或城市搜索网点地址与联系方式。"
        "若无该入口或搜索无结果，请点「转人工」。"
    )


def hours_body() -> str:
    return (
        "网点营业时间以 App「网点查询」中该网点详情页披露为准；"
        "本客服无法承诺具体开门或关门时刻。"
        "若详情页打不开或时间显示异常，请点「转人工」。"
    )


def cs_body() -> str:
    return (
        "在线客服／人工客服服务时间以 App 或官方渠道公布为准；"
        "本客服不口头承诺具体时段。"
        "若入口找不到或无法接通，请点「转人工」。"
    )


def _branch_reply(topic: str, seen: set[str]) -> tuple[dict[str, Any], set[str]]:
    bodies = {"find": find_body, "hours": hours_body, "cs": cs_body}
    graphics = {
        "find": "faq:branch_find",
        "hours": "faq:branch_hours",
        "cs": "faq:branch_cs",
    }
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
        "faq:branch_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def try_branch_dialogue(
    text: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    for key in _BUSY:
        if state.get(key, "idle") != "idle":
            return None, state

    branch = state.get("branch_flow", "idle")
    seen = _parse_seen(state.get("branch_seen"))

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
            "wealth_flow": "idle",
            "wealth_seen": "",
            "branch_flow": branch,
            "branch_seen": _dump_seen(seen),
        }
        base.update(kwargs)
        if "branch_seen" in kwargs and isinstance(kwargs["branch_seen"], set):
            base["branch_seen"] = _dump_seen(kwargs["branch_seen"])
        if "wealth_seen" in kwargs and isinstance(kwargs["wealth_seen"], set):
            base["wealth_seen"] = ",".join(
                k for k in ("doc", "risk", "yield") if k in kwargs["wealth_seen"]
            )
        return base

    def answer(topic: str) -> tuple[dict[str, Any], dict[str, Any]]:
        reply, new_seen = _branch_reply(topic, seen)
        if len(new_seen) >= len(TOPIC_ORDER):
            return reply, pack(branch_flow="idle", branch_seen="")
        return reply, pack(branch_flow="awaiting_clarify", branch_seen=new_seen)

    if branch == "awaiting_clarify":
        if _contains_any(text, HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(branch_flow="idle", branch_seen="")
        if _contains_any(text, DONE_KEYWORDS):
            return done_reply(), pack(branch_flow="idle", branch_seen="")
        if _contains_any(text, CS_HOURS_KEYWORDS):
            return answer("cs")
        if _contains_any(text, FIND_KEYWORDS):
            return answer("find")
        if _contains_any(text, HOURS_KEYWORDS):
            return answer("hours")
        if ff.should_keep_clarify_lock(text):
            return clarify_reply(), pack(branch_flow="awaiting_clarify", branch_seen=seen)
        # 未命中本场景：释放澄清态，避免换话题仍被同一句锁死
        return None, pack(branch_flow="idle", branch_seen="")

    if _contains_any(text, ASK_BRANCH_KEYWORDS):
        if _contains_any(text, HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(branch_flow="idle", branch_seen="")
        if _contains_any(text, CS_HOURS_KEYWORDS):
            return answer("cs")
        if _contains_any(text, FIND_KEYWORDS):
            return answer("find")
        if _contains_any(text, HOURS_KEYWORDS):
            return answer("hours")
        return clarify_reply(), pack(branch_flow="awaiting_clarify", branch_seen="")

    return None, state
