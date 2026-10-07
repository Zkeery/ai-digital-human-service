from __future__ import annotations

from typing import Any

DONE_KEYWORDS = ("不用了", "没有了", "先这样", "没了", "就这些", "暂时不用")
HUMAN_KEYWORDS = ("转人工", "人工客服", "找人工")

# 澄清追问中：仅这些「光杆词」继续本场景澄清，避免一两个字抢走话题；
# 完整句子／带细节的换话题应释放锁死。
_LOCK_PRESERVE_BARE = frozenset(
    {
        "银行卡",
        "信用卡",
        "转账",
        "理财",
        "网点",
        "密码",
        "账户",
        "投诉",
        "余额",
        "流水",
        "登录",
        "验证码",
    }
)


def should_keep_clarify_lock(text: str) -> bool:
    return text.strip() in _LOCK_PRESERVE_BARE


def parse_seen(raw: Any, valid: set[str] | frozenset[str] | dict[str, str]) -> set[str]:
    keys = set(valid) if not isinstance(valid, dict) else set(valid)
    if not raw:
        return set()
    if isinstance(raw, list):
        return {str(x) for x in raw if str(x) in keys}
    return {p for p in str(raw).split(",") if p in keys}


def dump_seen(seen: set[str], order: tuple[str, ...]) -> str:
    return ",".join(k for k in order if k in seen)


def follow_up(
    seen: set[str],
    labels: dict[str, str],
    order: tuple[str, ...],
    *,
    closing: str,
) -> str:
    remain = [labels[k] for k in order if k not in seen]
    if not remain:
        return closing
    parts = [f"「{x}」" for x in remain]
    if len(parts) == 1:
        joined = parts[0]
    elif len(parts) == 2:
        joined = f"{parts[0]}或{parts[1]}"
    else:
        joined = "、".join(parts[:-1]) + f"或{parts[-1]}"
    return f"您还想咨询{joined}吗？可继续点下方选项。"


def contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def topic_chips(
    order: tuple[str, ...],
    labels: dict[str, str],
    seen_raw: Any,
    *,
    cap: int = 5,
) -> list[dict[str, str]]:
    """未答过的主题标签；转人工只走顶栏入口，不在 chips 里重复。"""
    seen = parse_seen(seen_raw, labels)
    chips = [{"label": labels[k], "text": labels[k]} for k in order if k not in seen]
    return chips[:cap]
