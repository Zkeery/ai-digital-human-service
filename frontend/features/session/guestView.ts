import type { UiMode } from "./mode";

export const GUEST_TIP_DISMISS_PREFIX = "dh_guest_tip_dismissed:";

export const THEME_KEY = "dh_ui_theme";
/** 本标签页记住的会话 id，供刷新恢复；关闭标签即失效。 */
export const SESSION_KEY = "dh_session_id";
export const DEFAULT_GUIDE_TEXT =
  "您好，我是零售金融数字人客服。可咨询账户、转账、卡片、登录密码问题、信用卡、理财说明书、网点或投诉。请直接说明问题；查账、转账、改密等需本人在官方渠道办理。";

export function parseTheme(raw: string | null | undefined): "default" | "ink" {
  return raw === "ink" ? "ink" : "default";
}

export function parseStoredSessionId(raw: string | null | undefined): string | null {
  const value = (raw || "").trim();
  return value ? value : null;
}

export function shouldShowReplyMeta(mode: UiMode): boolean {
  return mode === "lab";
}

export function sessionStatusLabel(
  mode: UiMode,
  sessionId: string | null,
  status: string,
): string {
  if (!sessionId) return "尚未开始";
  if (status === "transferred") return "已转人工";
  if (mode === "guest") return "咨询中";
  return `会话 ${sessionId.slice(0, 8)}… · ${status}`;
}

export function showComposer(status: string, sessionId: string | null): boolean {
  return status === "active" && !!sessionId;
}

export function showEndedCard(status: string): boolean {
  return status === "transferred";
}

/** 转人工结束后仍允许再开一轮；仅发送中禁用。 */
export function canStartConsult(busy: boolean): boolean {
  return !busy;
}

export type BusyKind = "start" | "send" | null;

export type StatusCue = "starting" | "replying" | "replied" | "speaking" | null;

/** 发送反馈最短展示，避免本地规则秒回时用户看不到。 */
export const MIN_STATUS_CUE_MS = 2000;

/** 数字人画面状态：发送中／开始中覆盖「已就绪」等底稿。 */
export function avatarStatusHint(
  baseHint: string,
  busyKind: BusyKind,
  cue: StatusCue = null,
): string {
  if (busyKind === "send" || cue === "replying") return "回复中…";
  if (busyKind === "start" || cue === "starting") return "准备中…";
  if (cue === "speaking") return "本地口播中…";
  if (cue === "replied") return "已回复";
  return baseHint;
}

/** 发送后／状态条仍为回复中时，对话区展示占位气泡。 */
export function showPendingReply(busyKind: BusyKind, cue: StatusCue = null): boolean {
  return busyKind === "send" || cue === "replying";
}

/** 输入区旁的白话提示：为何暂时不能发（设计走查 #6：口播／回复中可视反馈）。 */
export function composerBusyHint(busyKind: BusyKind, cue: StatusCue = null): string | null {
  if (busyKind === "send" || cue === "replying") {
    return "客服正在回复／播报，发送已暂缓。请等文字出来后再发。";
  }
  if (busyKind === "start" || cue === "starting") return "正在开始咨询…";
  return null;
}

/** 回复／准备中：输入区视觉锁定（仍不允许打断发送）。 */
export function isReplyLocked(busyKind: BusyKind, cue: StatusCue = null): boolean {
  return busyKind === "send" || busyKind === "start" || cue === "replying" || cue === "starting";
}

/** 数字人画面角标：播报／准备状态一眼可见。 */
export function speakingBadgeLabel(busyKind: BusyKind, cue: StatusCue = null): string | null {
  if (busyKind === "send" || cue === "replying") return "回复播报中";
  if (cue === "speaking") return "本地口播中";
  if (busyKind === "start" || cue === "starting") return "准备中";
  if (cue === "replied") return "刚回复";
  return null;
}

/** 访客锁一屏并放大数字人画面；验收模式保持普通工作台（不给用户看，不强制锁屏）。 */
export function workspaceShellClass(mode: UiMode, themeClass: string): string {
  const parts = ["workspace"];
  if (themeClass) parts.push(themeClass);
  if (mode === "guest") {
    parts.push("shell-lock");
    parts.push("guest-shell");
  }
  return parts.join(" ");
}

/** 开始咨询后的连带发送：只接受非空字符串（忽略按钮 click 事件）。 */
export function followUpSendText(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

/** 输入区刚出现或回复锁定解除时，自动聚焦输入框（不抢滚动）。 */
export function shouldAutoFocusComposer(opts: {
  composerOn: boolean;
  locked: boolean;
  prevComposerOn: boolean;
  prevLocked: boolean;
}): boolean {
  if (!opts.composerOn || opts.locked) return false;
  if (!opts.prevComposerOn) return true;
  if (opts.prevLocked) return true;
  return false;
}

/** 取历史里最近一条非空客服回复，供一键复制。 */
export function latestAssistantText(
  history: ReadonlyArray<{ role: string; text: string }>,
): string {
  for (let i = history.length - 1; i >= 0; i -= 1) {
    const item = history[i];
    if (item.role !== "assistant") continue;
    const text = (item.text || "").trim();
    if (text) return text;
  }
  return "";
}

export function copyReplyButtonLabel(copied: boolean): string {
  return copied ? "已复制" : "复制回复";
}

/** 把本轮对话格式化成可粘贴文本（我／客服／欢迎）。 */
export function formatTranscript(
  history: ReadonlyArray<{ role: string; text: string; kind?: string }>,
): string {
  const lines: string[] = [];
  for (const item of history) {
    const text = (item.text || "").trim();
    if (!text) continue;
    let who = "客服";
    if (item.kind === "welcome") who = "欢迎";
    else if (item.role === "user") who = "我";
    else if (item.role === "assistant") who = "客服";
    lines.push(`${who}：${text}`);
  }
  return lines.join("\n\n");
}

export function copyTranscriptButtonLabel(copied: boolean): string {
  return copied ? "对话已复制" : "复制本轮对话";
}

/** 剪贴板不可用时的白话提示（不抛技术错误码）。 */
export const COPY_FAIL_HINT = "复制没成功。请长按气泡文字，手动选择后复制。";

/** 顶栏可见状态条文案。 */
export function statusCueLabel(cue: StatusCue): string | null {
  if (cue === "replying") return "客服回复中…请稍候";
  if (cue === "starting") return "正在开始咨询…";
  if (cue === "speaking") return "本地口播中（非现网直播）";
  if (cue === "replied") return "客服已回复";
  return null;
}

export function remainingHoldMs(startedAt: number, minMs: number, now = Date.now()): number {
  return Math.max(0, minMs - (now - startedAt));
}

/** 等浏览器先画出「回复中」，再发请求；本地秒回时否则永远看不见。 */
export function waitForPaint(ms = 0): Promise<void> {
  return new Promise((resolve) => {
    if (typeof requestAnimationFrame !== "function") {
      setTimeout(resolve, ms);
      return;
    }
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (ms <= 0) resolve();
        else setTimeout(resolve, ms);
      });
    });
  });
}

export function guestTipDismissKey(sessionId: string | null): string {
  return `${GUEST_TIP_DISMISS_PREFIX}${sessionId || "pending"}`;
}

export function isGuestTipDismissed(sessionId: string | null): boolean {
  if (typeof sessionStorage === "undefined") return false;
  return sessionStorage.getItem(guestTipDismissKey(sessionId)) === "1";
}

export function dismissGuestTip(sessionId: string | null): void {
  if (typeof sessionStorage === "undefined") return;
  sessionStorage.setItem(guestTipDismissKey(sessionId), "1");
}

/** 访客首屏提示：默认关闭，减少视觉负担；空态示例已说明怎么问。 */
export function shouldShowGuestTip(mode: UiMode, status: string, sessionId: string | null): boolean {
  void mode;
  void status;
  void sessionId;
  return false;
}
