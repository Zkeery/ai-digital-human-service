import type { EntryView } from "@/lib/api/session";

/** 解析建会话用的入口：访客固定默认；验收可用所选白名单入口。 */
export function resolveSessionEntryId(opts: {
  mode: "guest" | "lab";
  pilotEntryId: string;
  selectedEntryId: string | null;
  entries: EntryView[] | undefined;
}): string {
  const allowed = new Set((opts.entries || []).map((e) => e.id));
  if (opts.mode === "guest") {
    return allowed.has(opts.pilotEntryId) ? opts.pilotEntryId : opts.pilotEntryId;
  }
  const selected = (opts.selectedEntryId || "").trim();
  if (selected && allowed.has(selected)) return selected;
  if (allowed.has(opts.pilotEntryId)) return opts.pilotEntryId;
  return (opts.entries && opts.entries[0]?.id) || opts.pilotEntryId;
}

export function findEntry(
  entries: EntryView[] | undefined,
  entryId: string,
): EntryView | null {
  return (entries || []).find((e) => e.id === entryId) || null;
}

export function welcomeTextForEntry(
  entries: EntryView[] | undefined,
  entryId: string,
  fallback: string,
): string {
  const hit = findEntry(entries, entryId);
  const text = (hit?.welcome_text || "").trim();
  return text || fallback;
}

/** 访客壳不得渲染入口／Agent 配置控件。 */
export function showEntryAdminControls(mode: "guest" | "lab"): boolean {
  return mode === "lab";
}

/** 展示用：总闸×入口后的 Agent 是否会启用（配置预览，非访客控件）。 */
export function effectiveAgentPreview(globalOn: boolean, entry: EntryView | null): boolean {
  return Boolean(globalOn && entry?.agent_enabled);
}

export function safeAccent(raw: string | undefined, fallback = "#0f766e"): string {
  const value = (raw || "").trim();
  if (/^#[0-9a-fA-F]{6}$/.test(value)) return value;
  return fallback;
}

export function safeLogoUrl(raw: string | undefined): string {
  const value = (raw || "").trim();
  if (!value) return "";
  if (value.startsWith("/entries/") && !value.includes("..")) return value;
  return "";
}
