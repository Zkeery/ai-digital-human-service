"use client";

import type { UiMode } from "../mode";

type Props = {
  mode: UiMode;
  onChange: (mode: UiMode) => void;
};

export function ModeSwitch({ mode, onChange }: Props) {
  return (
    <div className="mode-switch">
      {mode === "guest" ? (
        <button
          type="button"
          className="guest-tool-link mode-switch-link"
          onClick={() => onChange("lab")}
        >
          验收
        </button>
      ) : (
        <>
          <span className="mode-badge">验收模式</span>
          <button type="button" className="btn ghost mode-switch-btn" onClick={() => onChange("guest")}>
            返回访客
          </button>
        </>
      )}
    </div>
  );
}
