import type { SessionEvent } from "@/lib/api/session";

export type { SessionEvent };

/** 把事件收成一行可读文案（lab 时间线用）。 */
export function formatEventLine(ev: SessionEvent): string {
  const time = (ev.created_at || "").replace("T", " ").slice(0, 19);
  const key = ev.event_key || "unknown";
  const payload = ev.payload && typeof ev.payload === "object" ? ev.payload : {};
  const hintKeys = ["reason", "source", "by", "entry_id", "return_flow", "refund_flow"];
  const bits: string[] = [];
  for (const k of hintKeys) {
    const v = (payload as Record<string, unknown>)[k];
    if (v === undefined || v === null || v === "") continue;
    bits.push(`${k}=${String(v)}`);
    if (bits.length >= 2) break;
  }
  const extra = bits.length ? ` · ${bits.join(", ")}` : "";
  return `${time || "—"}  ${key}${extra}`;
}

export function sortEventsNewestFirst(items: SessionEvent[]): SessionEvent[] {
  return [...items].sort((a, b) => {
    if (a.created_at === b.created_at) return b.id - a.id;
    return a.created_at < b.created_at ? 1 : -1;
  });
}
