import type { HistoryItem } from "@/lib/api/session";

/** 用本会话发送时记住的原文覆盖历史里的用户气泡（避免落库脱敏 **** 盖住刚打的字）。 */
export function applyLocalUserEchoes(
  items: HistoryItem[],
  echoes: string[],
): HistoryItem[] {
  if (!echoes.length) return items;
  const userPositions = items
    .map((item, index) => (item.role === "user" ? index : -1))
    .filter((index) => index >= 0);
  const aligned = echoes.slice(-userPositions.length);
  let echoAt = 0;
  return items.map((item) => {
    if (item.role !== "user") return item;
    const text = aligned[echoAt] ?? item.text;
    echoAt += 1;
    return { ...item, text };
  });
}

/**
 * 开场欢迎只标在「第一条用户发言之前」；之后即使寒暄文案相同，也显示「客服」。
 * 历史里若没有开场欢迎，则前置一条本地欢迎气泡。
 */
export function applyWelcomeBubble(
  items: HistoryItem[],
  welcome: string | null,
): HistoryItem[] {
  const base = items.map((item) => ({
    ...item,
    kind: item.kind === "welcome" ? ("chat" as const) : item.kind || ("chat" as const),
  }));
  if (!welcome) return base;

  let seenUser = false;
  let marked = false;
  const mapped = base.map((item) => {
    if (item.role === "user") seenUser = true;
    if (
      !marked &&
      !seenUser &&
      item.role === "assistant" &&
      item.text === welcome
    ) {
      marked = true;
      return { ...item, kind: "welcome" as const };
    }
    return item;
  });

  if (marked) return mapped;
  return [
    {
      role: "assistant",
      text: welcome,
      created_at: new Date(0).toISOString(),
      kind: "welcome",
    },
    ...mapped,
  ];
}
