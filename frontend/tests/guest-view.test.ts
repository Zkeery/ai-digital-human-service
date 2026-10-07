import { describe, expect, it, vi } from "vitest";
import {
  DEFAULT_GUIDE_TEXT,
  parseTheme,
  parseStoredSessionId,
  sessionStatusLabel,
  shouldShowReplyMeta,
  showComposer,
  showEndedCard,
  canStartConsult,
  avatarStatusHint,
  showPendingReply,
  composerBusyHint,
  isReplyLocked,
  speakingBadgeLabel,
  workspaceShellClass,
  followUpSendText,
  shouldAutoFocusComposer,
  latestAssistantText,
  copyReplyButtonLabel,
  formatTranscript,
  copyTranscriptButtonLabel,
  COPY_FAIL_HINT,
  statusCueLabel,
  remainingHoldMs,
  waitForPaint,
  guestTipDismissKey,
  dismissGuestTip,
  isGuestTipDismissed,
  shouldShowGuestTip,
} from "../features/session/guestView";

describe("guest view helpers", () => {
  it("hides technical meta in guest", () => {
    expect(shouldShowReplyMeta("guest")).toBe(false);
  });

  it("welcome copy is retail finance", () => {
    expect(DEFAULT_GUIDE_TEXT).toContain("零售金融");
    expect(DEFAULT_GUIDE_TEXT).toContain("账户");
    expect(DEFAULT_GUIDE_TEXT).toContain("登录密码问题");
    expect(DEFAULT_GUIDE_TEXT).not.toContain("退货");
  });

  it("shows consult label instead of raw id in guest", () => {
    expect(sessionStatusLabel("guest", "abcdef12-xxxx", "active")).toBe("咨询中");
    expect(sessionStatusLabel("guest", "abcdef12-xxxx", "transferred")).toBe("已转人工");
  });

  it("hides composer after transfer but allows restart", () => {
    expect(showComposer("active", "s1")).toBe(true);
    expect(showComposer("transferred", "s1")).toBe(false);
    expect(showEndedCard("transferred")).toBe(true);
    expect(canStartConsult(false)).toBe(true);
    expect(canStartConsult(true)).toBe(false);
  });

  it("parses stored session id", () => {
    expect(parseStoredSessionId(null)).toBeNull();
    expect(parseStoredSessionId("  ")).toBeNull();
    expect(parseStoredSessionId(" abc-123 ")).toBe("abc-123");
  });

  it("parses theme", () => {
    expect(parseTheme(null)).toBe("default");
    expect(parseTheme("ink")).toBe("ink");
  });

  it("maps busy kind to avatar / pending / composer hints", () => {
    expect(avatarStatusHint("已就绪", null)).toBe("已就绪");
    expect(avatarStatusHint("已就绪", "send")).toBe("回复中…");
    expect(avatarStatusHint("已就绪", "start")).toBe("准备中…");
    expect(avatarStatusHint("已就绪", null, "replied")).toBe("已回复");
    expect(avatarStatusHint("已就绪", null, "speaking")).toBe("本地口播中…");
    expect(speakingBadgeLabel(null, "speaking")).toBe("本地口播中");
    expect(statusCueLabel("speaking")).toContain("本地口播");
    expect(isReplyLocked(null, "speaking")).toBe(false);
    expect(showPendingReply("send")).toBe(true);
    expect(showPendingReply(null)).toBe(false);
    expect(showPendingReply(null, "replying")).toBe(true);
    expect(composerBusyHint("send")).toContain("发送已暂缓");
    expect(composerBusyHint(null, "replying")).toContain("播报");
    expect(composerBusyHint("start")).toContain("开始");
    expect(composerBusyHint(null)).toBeNull();
    expect(isReplyLocked("send")).toBe(true);
    expect(isReplyLocked(null, "replying")).toBe(true);
    expect(isReplyLocked(null)).toBe(false);
    expect(speakingBadgeLabel("send")).toBe("回复播报中");
    expect(speakingBadgeLabel(null, "starting")).toBe("准备中");
    expect(speakingBadgeLabel(null)).toBeNull();
    expect(workspaceShellClass("guest", "theme-ink")).toContain("guest-shell");
    expect(workspaceShellClass("guest", "theme-ink")).toContain("shell-lock");
    expect(workspaceShellClass("guest", "theme-ink")).toContain("theme-ink");
    expect(workspaceShellClass("lab", "")).toBe("workspace");
    expect(workspaceShellClass("lab", "")).not.toContain("shell-lock");
    expect(followUpSendText("查余额")).toBe("查余额");
    expect(followUpSendText({ type: "click" })).toBe("");
    expect(followUpSendText(undefined)).toBe("");
    expect(
      shouldAutoFocusComposer({
        composerOn: true,
        locked: false,
        prevComposerOn: false,
        prevLocked: true,
      }),
    ).toBe(true);
    expect(
      shouldAutoFocusComposer({
        composerOn: true,
        locked: false,
        prevComposerOn: true,
        prevLocked: true,
      }),
    ).toBe(true);
    expect(
      shouldAutoFocusComposer({
        composerOn: true,
        locked: true,
        prevComposerOn: true,
        prevLocked: false,
      }),
    ).toBe(false);
    expect(
      shouldAutoFocusComposer({
        composerOn: true,
        locked: false,
        prevComposerOn: true,
        prevLocked: false,
      }),
    ).toBe(false);
    expect(
      latestAssistantText([
        { role: "user", text: "查余额" },
        { role: "assistant", text: "请到官方 App 查询余额" },
        { role: "user", text: "好的" },
      ]),
    ).toBe("请到官方 App 查询余额");
    expect(latestAssistantText([{ role: "user", text: "hi" }])).toBe("");
    expect(copyReplyButtonLabel(false)).toBe("复制回复");
    expect(copyReplyButtonLabel(true)).toBe("已复制");
    expect(
      formatTranscript([
        { role: "assistant", text: "您好", kind: "welcome" },
        { role: "user", text: "查余额" },
        { role: "assistant", text: "请到官方 App 查询" },
      ]),
    ).toBe("欢迎：您好\n\n我：查余额\n\n客服：请到官方 App 查询");
    expect(formatTranscript([])).toBe("");
    expect(copyTranscriptButtonLabel(false)).toBe("复制本轮对话");
    expect(copyTranscriptButtonLabel(true)).toBe("对话已复制");
    expect(COPY_FAIL_HINT).toContain("长按");
    expect(COPY_FAIL_HINT).not.toMatch(/clipboard|navigator|error/i);
    expect(statusCueLabel("replying")).toContain("回复中");
    expect(statusCueLabel("replied")).toContain("已回复");
    expect(remainingHoldMs(Date.now() - 100, 1200)).toBeGreaterThan(900);
    expect(remainingHoldMs(Date.now() - 2000, 1200)).toBe(0);
  });

  it("waitForPaint resolves", async () => {
    await expect(waitForPaint(0)).resolves.toBeUndefined();
  });

  it("guest tip dismiss is per consultation session", () => {
    const store = new Map<string, string>();
    vi.stubGlobal("sessionStorage", {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => {
        store.set(k, v);
      },
      removeItem: (k: string) => {
        store.delete(k);
      },
      clear: () => store.clear(),
    });
    // 访客提示默认关闭，避免首屏信息过载；dismiss 状态仍可持久化备用
    expect(shouldShowGuestTip("guest", "active", "sess-a")).toBe(false);
    dismissGuestTip("sess-a");
    expect(isGuestTipDismissed("sess-a")).toBe(true);
    expect(shouldShowGuestTip("guest", "active", "sess-b")).toBe(false);
    expect(guestTipDismissKey(null)).toContain("pending");
    expect(shouldShowGuestTip("lab", "active", "sess-a")).toBe(false);
    expect(shouldShowGuestTip("guest", "transferred", "sess-a")).toBe(false);
    vi.unstubAllGlobals();
  });
});
