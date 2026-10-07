import type { UiMode } from "./mode";
import { ApiError } from "@/lib/api/client";
import { formatApiError, type ErrorAudience } from "@/lib/api/errors";

export type BannerKind = "ok" | "err" | "warn";
export type BannerTone = "default" | "rate" | "network";
export type BannerRetry = "start" | "send";
export type Banner = {
  kind: BannerKind;
  text: string;
  tone?: BannerTone;
  /** 访客失败可恢复：顶栏提供「重试」 */
  retry?: BannerRetry;
};

/** 成功短时消失；警告稍久；错误需手动关。限流警告可自动关。 */
export function autoDismissMs(kind: BannerKind, tone: BannerTone = "default"): number | null {
  if (kind === "ok") return 3200;
  if (kind === "warn") return tone === "rate" ? 10000 : 8000;
  return null;
}

/** 访客日常操作成功不弹绿条，避免挡对话。 */
export function shouldAnnounceSuccess(mode: UiMode, label: string): boolean {
  if (mode !== "guest") return true;
  return label !== "发送" && label !== "开始咨询";
}

export function bannerClassName(banner: Banner): string {
  const tone = banner.tone && banner.tone !== "default" ? ` banner-tone-${banner.tone}` : "";
  return `banner banner-${banner.kind}${tone}`;
}

function isNetworkFailure(err: unknown): boolean {
  if (!(err instanceof Error)) return false;
  const msg = err.message.toLowerCase();
  return (
    err.name === "TypeError" ||
    msg.includes("failed to fetch") ||
    msg.includes("networkerror") ||
    msg.includes("load failed") ||
    msg.includes("network request failed")
  );
}

/** 按错误类型选条样式：限流用警告色，网络失败用错误色。 */
export function errorBanner(
  err: unknown,
  audience: ErrorAudience,
  retry?: BannerRetry,
): Banner {
  const text = formatApiError(err, { audience });
  if (err instanceof ApiError && err.code === "RATE_LIMITED") {
    return { kind: "warn", text, tone: "rate", retry };
  }
  if (isNetworkFailure(err)) {
    return { kind: "err", text, tone: "network", retry };
  }
  return { kind: "err", text, tone: "default", retry };
}

/** 空态示例标签：未开会话则先开始再发；咨询中直接发。 */
export function emptyHintAction(
  sessionId: string | null,
  status: string,
): "start_then_send" | "send" | "none" {
  if (status === "transferred") return "none";
  if (sessionId && status === "active") return "send";
  return "start_then_send";
}

export type EmptyChatState = {
  title: string;
  body: string;
  hints: string[];
  loading: boolean;
};

export function emptyChatState(opts: {
  sessionId: string | null;
  busyStart: boolean;
}): EmptyChatState {
  if (opts.busyStart) {
    return {
      title: "正在准备咨询…",
      body: "稍等片刻，马上就可以提问。",
      hints: [],
      loading: true,
    };
  }
  if (opts.sessionId) {
    return {
      title: "可以说出你的问题",
      body: "直接输入，或点下方示例问题。",
      hints: ["查余额", "办信用卡", "网点在哪"],
      loading: false,
    };
  }
  return {
    title: "开始金融咨询",
    body: "可点「开始咨询」，或直接点下方示例问题（会自动开始）。",
    hints: ["查余额", "办信用卡", "网点营业时间"],
    loading: false,
  };
}
