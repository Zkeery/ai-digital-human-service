export type UiMode = "guest" | "lab";

export const UI_MODE_KEY = "dh_ui_mode";

export function parseUiMode(raw: string | null | undefined): UiMode {
  return raw === "lab" ? "lab" : "guest";
}

export function guestHiddenControls(): string[] {
  return [
    "agent-toggle",
    "push",
    "stream-started",
    "check-sync",
    "simulate-fallback",
    "special-commands",
  ];
}

export function isControlVisible(mode: UiMode, controlId: string): boolean {
  if (mode === "lab") return true;
  return !guestHiddenControls().includes(controlId);
}
