import { ApiError } from "./client";

export type ErrorAudience = "guest" | "lab";

const GUEST_BY_CODE: Record<string, string> = {
  SESSION_NOT_ACTIVE: "本轮咨询已结束。如需继续，请点「重新开始咨询」。",
  SESSION_NOT_FOUND: "会话已失效。请重新开始咨询。",
  VALIDATION_ERROR: "输入不太合适，请换个说法再试。",
  RATE_LIMITED: "当前咨询较多，请稍后再试。",
  BUDGET_EXCEEDED: "今日智能助手额度已用完，仍可继续基础咨询或转人工。",
};

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

/** lab 保留码；guest 只出口语，不拼技术码。 */
export function formatApiError(
  err: unknown,
  opts?: { audience?: ErrorAudience },
): string {
  const audience = opts?.audience ?? "lab";

  if (isNetworkFailure(err)) {
    return audience === "guest"
      ? "暂时连不上客服，请检查网络后重试。"
      : `网络请求失败：${err instanceof Error ? err.message : "unknown"}`;
  }

  if (err instanceof ApiError) {
    if (audience === "guest") {
      return GUEST_BY_CODE[err.code] || err.message || "出了点问题，请稍后再试。";
    }
    return `${err.message}（${err.code}）`;
  }

  if (err instanceof Error) {
    return audience === "guest" ? "出了点问题，请稍后再试。" : err.message;
  }

  return audience === "guest" ? "出了点问题，请稍后再试。" : "未知错误";
}
