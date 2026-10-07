/** 本地形象静帧（非现网 RTC 推流画面）。 */

const ALLOWED = new Set(["001", "002", "003", "004"]);

export function normalizeProfileKey(raw: string | null | undefined): string {
  const key = (raw || "").trim();
  return ALLOWED.has(key) ? key : "001";
}

export function profileAvatarSrc(raw: string | null | undefined): string {
  return `/avatars/${normalizeProfileKey(raw)}.svg`;
}

export function profileAvatarAlt(raw: string | null | undefined, entryLabel = ""): string {
  const key = normalizeProfileKey(raw);
  return entryLabel ? `${entryLabel} · 形象 ${key}` : `形象 ${key}`;
}
