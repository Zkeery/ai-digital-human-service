import type { QuickReply } from "@/lib/api/session";

/** @deprecated 开场不再铺入口；仅作文案对照。 */
export const PRIMARY_STARTER_QUICK_REPLIES: QuickReply[] = [
  { label: "查余额", text: "查余额" },
  { label: "查流水", text: "查流水" },
  { label: "转账失败", text: "转账失败" },
  { label: "银行卡", text: "银行卡" },
  { label: "忘记密码", text: "忘记密码" },
];

/** @deprecated 同上。 */
export const MORE_STARTER_QUICK_REPLIES: QuickReply[] = [
  { label: "信用卡", text: "信用卡" },
  { label: "理财说明", text: "理财说明" },
  { label: "网点营业时间", text: "营业时间" },
  { label: "我要投诉", text: "我要投诉" },
];

/** @deprecated 开场不再默认展示全部入口。 */
export const STARTER_QUICK_REPLIES: QuickReply[] = [
  ...PRIMARY_STARTER_QUICK_REPLIES,
  ...MORE_STARTER_QUICK_REPLIES,
];

const CHIP_CAP = 5;
const TRANSFER_CHIP_LABELS = new Set(["转人工", "人工客服", "找人工"]);

/** 规范化后端 quick_replies：按用户问到的流程关键词下发，最多 5 个；去掉与顶栏重复的转人工。 */
export function normalizeQuickReplies(items: unknown): QuickReply[] {
  if (!Array.isArray(items)) return [];
  const out: QuickReply[] = [];
  for (const raw of items) {
    if (!raw || typeof raw !== "object") continue;
    const label = String((raw as QuickReply).label || "").trim();
    const text = String((raw as QuickReply).text || label).trim();
    if (!label || !text) continue;
    if (TRANSFER_CHIP_LABELS.has(label) || TRANSFER_CHIP_LABELS.has(text)) continue;
    out.push({ label, text });
    if (out.length >= CHIP_CAP) break;
  }
  return out;
}

export function shouldShowQuickReplies(
  status: string,
  replies: QuickReply[] | undefined | null,
): boolean {
  if (status !== "active") return false;
  return normalizeQuickReplies(replies || []).length > 0;
}

export type DisplayedQuickReplies = {
  primary: QuickReply[];
  more: QuickReply[];
  isStarter: boolean;
};

/**
 * 只展示后端按对话状态给出的关键词选项；开场不再铺一排入口。
 */
export function resolveDisplayedQuickReplies(opts: {
  status: string;
  canChat: boolean;
  backendReplies?: QuickReply[] | null;
}): DisplayedQuickReplies {
  if (opts.status !== "active" || !opts.canChat) {
    return { primary: [], more: [], isStarter: false };
  }
  const backend = normalizeQuickReplies(opts.backendReplies || []);
  return { primary: backend, more: [], isStarter: false };
}
