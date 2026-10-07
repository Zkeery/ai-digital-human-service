from __future__ import annotations

# 确定性 FAQ／规则主路径（零售金融样例，不接现网知识库）

FAQ_RULES: list[dict[str, str]] = [
    {
        "keywords": "你好,您好,在吗",
        "spoken_text": (
            "您好，我是零售金融数字人客服。"
            "可咨询账户、转账、卡片、登录密码问题、信用卡、理财说明书、网点或投诉。"
            "请直接说明问题；查账、转账、改密等需本人在官方渠道办理。"
        ),
        "graphic_template_ref": "faq:greeting",
        "action_intent": "wave",
    },
]

# 历史电商样例关键词：明示业务边界，不进入旧退货等流程
ECOMMERCE_OFFTOPIC_KEYWORDS = (
    "退货",
    "换货",
    "退款进度",
    "查物流",
    "物流",
    "快递",
    "优惠券",
    "价保",
    "缺货",
    "到货通知",
    "开发票",
    "开票",
    "取消订单",
    "改地址",
    "修改地址",
    "保修",
    "质保",
    "会员积分",
    "怎么退",
    "我要退",
)


def _hit(keywords: str | tuple[str, ...], text: str) -> bool:
    normalized = text.strip().lower()
    items = keywords.split(",") if isinstance(keywords, str) else keywords
    return any(k.strip().lower() in normalized for k in items if k.strip())


def match_ecommerce_offtopic(text: str) -> dict[str, str] | None:
    if not _hit(ECOMMERCE_OFFTOPIC_KEYWORDS, text):
        return None
    return {
        "spoken_text": (
            "我是零售金融数字人客服，不办理网购售后（退货、物流、优惠券、价保等）。"
            "您可以问账户、转账、卡片、登录密码问题、信用卡、理财说明书、网点或投诉；"
            "需要同事协助请点「转人工」。"
        ),
        "graphic_template_ref": "faq:offtopic_ecommerce",
        "action_intent": "none",
    }


def match_faq(text: str) -> dict[str, str] | None:
    for rule in FAQ_RULES:
        if _hit(rule["keywords"], text):
            return {
                "spoken_text": rule["spoken_text"],
                "graphic_template_ref": rule["graphic_template_ref"],
                "action_intent": rule["action_intent"],
            }
    return None


def match_aside(text: str) -> tuple[dict[str, str] | None, str | None]:
    """确定性旁路：电商偏题优先于寒暄 FAQ。返回 (hit, source_tag)。"""
    offtopic = match_ecommerce_offtopic(text)
    if offtopic:
        return offtopic, "offtopic_rule"
    hit = match_faq(text)
    if hit:
        return hit, "faq"
    return None, None


def default_fallback_reply() -> dict[str, str]:
    return {
        "spoken_text": (
            "我这边主要帮您了解零售金融咨询指引。"
            "您可以说「查余额」「办信用卡」「网点在哪」或「我要投诉」；"
            "需要同事协助请点「转人工」。"
        ),
        "graphic_template_ref": "faq:fallback",
        "action_intent": "none",
    }
