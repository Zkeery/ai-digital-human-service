from __future__ import annotations

from typing import Any

from app.services import finance_followup as ff
from app.services import return_dialogue as rd

# 信用卡：顶层（办卡／额度／还款／提额）+ 办卡子流程（卡种／材料／步骤）

ASK_CREDIT_KEYWORDS = (
    "信用卡",
    "办信用卡",
    "申请信用卡",
    "怎么办信用卡",
    "怎么申请信用卡",
    "办卡",
    "申请办卡",
    "开信用卡",
    "新办信用卡",
    "我想办信用卡",
    "信用额度",
    "可用额度",
    "查额度",
    "还款",
    "还款日",
    "信用卡还款",
    "账单还款",
    "怎么还款",
    "还款与账单",
    "提额",
    "提升额度",
    "申请提额",
    "降额",
)
APPLY_ENTRY_KEYWORDS = (
    "办卡申请",
    "办信用卡",
    "申请信用卡",
    "怎么办信用卡",
    "怎么申请信用卡",
    "申请办卡",
    "开信用卡",
    "新办信用卡",
    "我想办信用卡",
    "我要办信用卡",
    "办张信用卡",
    "办卡",
)
APPLY_PICK_KEYWORDS = ("卡种怎么选", "选卡种", "什么卡", "有哪些卡", "卡种与权益", "办什么卡")
APPLY_DOCS_KEYWORDS = ("申请材料", "需要什么材料", "要交什么", "准备什么资料", "办卡材料")
APPLY_STEPS_KEYWORDS = ("申请步骤", "怎么办", "怎么申请", "申请流程", "办理步骤", "怎么提交")
LIMIT_KEYWORDS = ("查额度", "信用额度", "可用额度", "看额度", "额度多少")
REPAY_KEYWORDS = (
    "还款与账单",
    "还款日怎么还",
    "还款日",
    "信用卡还款",
    "账单还款",
    "怎么还款",
    "何时还款",
    "查还款日",
    "还款",
)
RAISE_KEYWORDS = (
    "申请提额",
    "提额疑问",
    "提额",
    "提升额度",
    "降额",
    "额度降了",
)

# 顶层选项
TOP_LABELS = {
    "apply": "办卡申请",
    "limit": "查额度",
    "repay": "还款与账单",
    "raise": "申请提额",
}
TOP_ORDER = ("apply", "limit", "repay", "raise")

# 办卡子弹层选项
APPLY_LABELS = {
    "pick": "卡种怎么选",
    "docs": "申请材料",
    "steps": "申请步骤",
}
APPLY_ORDER = ("pick", "docs", "steps")

_BUSY = (
    "account_flow",
    "transfer_flow",
    "card_flow",
    "auth_flow",
    "wealth_flow",
    "branch_flow",
    "complaint_flow",
)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "请问您要办卡申请、查额度、看还款账单，还是申请提额？点下方选项即可。",
        "faq:credit_clarify",
        action="none",
    )


def apply_clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "好的，办理信用卡可以按下面了解：卡种怎么选、申请需要什么材料，以及申请步骤。请点下方选项。",
        "faq:credit_apply_clarify",
        action="none",
    )


def done_reply() -> dict[str, Any]:
    return rd._reply(
        "好的。如还有信用卡问题，可随时再问；需要同事协助请点「转人工」。",
        "faq:credit_done",
        action="none",
        suggest_transfer=True,
    )


def pick_body() -> str:
    return (
        "可申请的卡种、权益与申请条件，以 App「信用卡」→「申请办卡」或「卡片申请」页面实时展示为准。"
        "请按页面对比卡种后选择；本客服不能代您选定卡种，也不能承诺权益是否适合您。"
        "若页面打不开或列表为空，请点「转人工」。"
    )


def docs_body() -> str:
    return (
        "申请材料以办卡页面提示为准，通常需本人有效身份证件，并按页面填写职业、联系方式等资料。"
        "请勿把完整身份证号、验证码发给客服。"
        "若页面要求补充材料但您不确定如何上传，请点「转人工」。"
    )


def steps_body() -> str:
    return (
        "申请步骤：打开 App →「信用卡」→「申请办卡」或「卡片申请」→ 选择卡种 → 按页填写并提交。"
        "是否批核、初始额度以银行审核为准；本客服不能代办申请，也不能承诺批卡结果或额度。"
        "若提交失败或一直审核中需要查询，请点「转人工」。"
    )


def limit_body() -> str:
    return (
        "请打开 App，依次进入「信用卡」→「卡片管理」或「我的额度」，"
        "页面会显示总额度与可用额度。"
        "若入口不在或页面报错，请点「转人工」。请勿发送完整卡号。"
    )


def repay_body() -> str:
    return (
        "打开 App「信用卡－账单」，可查看本期还款日与应还金额，"
        "并选择最低应还或全额还款。"
        "若找不到账单入口或自动扣款失败，请点「转人工」。"
    )


def raise_body() -> str:
    return (
        "请在 App「信用卡」中提交提额申请，由银行系统审核；"
        "客服无法预定或改写审核结果。"
        "若没有申请入口，或额度被下调需要核对原因，请点「转人工」。"
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "好的，请点「转人工」，我帮您接通同事。",
        "faq:credit_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def _topic_reply(
    topic: str,
    seen: set[str],
    *,
    bodies: dict[str, Any],
    graphics: dict[str, str],
    labels: dict[str, str],
    order: tuple[str, ...],
    closing: str,
) -> tuple[dict[str, Any], set[str]]:
    new_seen = set(seen)
    new_seen.add(topic)
    spoken = bodies[topic]() + ff.follow_up(
        new_seen,
        labels,
        order,
        closing=closing,
    )
    return (
        rd._reply(spoken, graphics[topic], action="none", suggest_transfer=True),
        new_seen,
    )


def try_credit_dialogue(
    text: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    for key in _BUSY:
        if state.get(key, "idle") != "idle":
            return None, state

    credit = state.get("credit_flow", "idle")
    seen = ff.parse_seen(state.get("credit_seen"), {**TOP_LABELS, **APPLY_LABELS})

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
            "card_flow": "idle",
            "card_seen": "",
            "auth_flow": "idle",
            "auth_seen": "",
            "credit_flow": credit,
            "credit_seen": ff.dump_seen(seen, TOP_ORDER + APPLY_ORDER),
            "wealth_flow": "idle",
            "wealth_seen": "",
            "branch_flow": "idle",
            "branch_seen": "",
        }
        base.update(kwargs)
        if "credit_seen" in kwargs and isinstance(kwargs["credit_seen"], set):
            base["credit_seen"] = ff.dump_seen(kwargs["credit_seen"], TOP_ORDER + APPLY_ORDER)
        return base

    def answer_top(topic: str) -> tuple[dict[str, Any], dict[str, Any]]:
        reply, new_seen = _topic_reply(
            topic,
            seen,
            bodies={"limit": limit_body, "repay": repay_body, "raise": raise_body},
            graphics={
                "limit": "faq:credit_limit",
                "repay": "faq:credit_repay",
                "raise": "faq:credit_raise",
            },
            labels=TOP_LABELS,
            order=TOP_ORDER,
            closing="如还需核对信用卡事项，请点「转人工」，或直接说其他问题。",
        )
        # 顶层答完额度／还款／提额后，仍可回办卡；seen 只记顶层三项
        top_seen = {k for k in new_seen if k in TOP_LABELS}
        if len(top_seen) >= len(TOP_ORDER):
            return reply, pack(credit_flow="idle", credit_seen="")
        return reply, pack(credit_flow="awaiting_clarify", credit_seen=top_seen)

    def answer_apply(topic: str) -> tuple[dict[str, Any], dict[str, Any]]:
        reply, new_seen = _topic_reply(
            topic,
            {k for k in seen if k in APPLY_LABELS},
            bodies={"pick": pick_body, "docs": docs_body, "steps": steps_body},
            graphics={
                "pick": "faq:credit_apply_pick",
                "docs": "faq:credit_apply_docs",
                "steps": "faq:credit_apply_steps",
            },
            labels=APPLY_LABELS,
            order=APPLY_ORDER,
            closing="办卡指引已说完。如需查额度或还款，可直接说明；需要同事协助请点「转人工」。",
        )
        apply_seen = {k for k in new_seen if k in APPLY_LABELS}
        if len(apply_seen) >= len(APPLY_ORDER):
            return reply, pack(credit_flow="idle", credit_seen="")
        return reply, pack(credit_flow="awaiting_apply", credit_seen=apply_seen)

    def enter_apply() -> tuple[dict[str, Any], dict[str, Any]]:
        return apply_clarify_reply(), pack(credit_flow="awaiting_apply", credit_seen="")

    if credit == "awaiting_apply":
        if ff.contains_any(text, ff.HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(credit_flow="idle", credit_seen="")
        if ff.contains_any(text, ff.DONE_KEYWORDS):
            return done_reply(), pack(credit_flow="idle", credit_seen="")
        if ff.contains_any(text, APPLY_PICK_KEYWORDS):
            return answer_apply("pick")
        if ff.contains_any(text, APPLY_DOCS_KEYWORDS):
            return answer_apply("docs")
        if ff.contains_any(text, APPLY_STEPS_KEYWORDS):
            return answer_apply("steps")
        # 办卡子弹层里改问额度／还款／提额 → 回到顶层作答
        if ff.contains_any(text, RAISE_KEYWORDS):
            return answer_top("raise")
        if ff.contains_any(text, REPAY_KEYWORDS):
            return answer_top("repay")
        if ff.contains_any(text, LIMIT_KEYWORDS):
            return answer_top("limit")
        if ff.should_keep_clarify_lock(text):
            return apply_clarify_reply(), pack(credit_flow="awaiting_apply", credit_seen=seen)
        return None, pack(credit_flow="idle", credit_seen="")

    if credit == "awaiting_clarify":
        if ff.contains_any(text, ff.HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(credit_flow="idle", credit_seen="")
        if ff.contains_any(text, ff.DONE_KEYWORDS):
            return done_reply(), pack(credit_flow="idle", credit_seen="")
        if ff.contains_any(text, APPLY_ENTRY_KEYWORDS):
            return enter_apply()
        if ff.contains_any(text, RAISE_KEYWORDS):
            return answer_top("raise")
        if ff.contains_any(text, REPAY_KEYWORDS):
            return answer_top("repay")
        if ff.contains_any(text, LIMIT_KEYWORDS):
            return answer_top("limit")
        if ff.should_keep_clarify_lock(text):
            return clarify_reply(), pack(credit_flow="awaiting_clarify", credit_seen=seen)
        return None, pack(credit_flow="idle", credit_seen="")

    if ff.contains_any(text, ASK_CREDIT_KEYWORDS):
        if ff.contains_any(text, ff.HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(credit_flow="idle", credit_seen="")
        if ff.contains_any(text, APPLY_ENTRY_KEYWORDS):
            return enter_apply()
        if ff.contains_any(text, RAISE_KEYWORDS):
            return answer_top("raise")
        if ff.contains_any(text, REPAY_KEYWORDS):
            return answer_top("repay")
        if ff.contains_any(text, LIMIT_KEYWORDS):
            return answer_top("limit")
        return clarify_reply(), pack(credit_flow="awaiting_clarify", credit_seen="")

    return None, state
