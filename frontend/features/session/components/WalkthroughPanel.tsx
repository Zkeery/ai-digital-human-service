"use client";

import {
  PRODUCT_WALKTHROUGH_ITEMS,
  isWalkthroughTransfer,
  type WalkthroughItem,
} from "../walkthrough";

type Props = {
  busy: boolean;
  canChat: boolean;
  onRun: (item: WalkthroughItem) => void;
};

export function WalkthroughPanel({ busy, canChat, onRun }: Props) {
  return (
    <section className="walkthrough-panel" aria-label="产品走查快捷条">
      <div className="walkthrough-head">
        <h2>产品走查快捷条</h2>
        <p className="hint">对照《产品走查清单》#2～#4／#6／#8；未开会话时会先自动开始。</p>
      </div>
      <div className="chip-row walkthrough-chips" role="group" aria-label="走查例句">
        {PRODUCT_WALKTHROUGH_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`btn ghost walkthrough-chip${item.id === "return" ? " walkthrough-offtopic" : ""}${isWalkthroughTransfer(item) ? " danger-outline" : ""}`}
            disabled={busy || (isWalkthroughTransfer(item) && !canChat)}
            title={isWalkthroughTransfer(item) ? "打开转人工确认" : `将发送：${item.text}`}
            onClick={() => onRun(item)}
          >
            <span className="walkthrough-chip-label">{item.label}</span>
            {!isWalkthroughTransfer(item) ? (
              <span className="walkthrough-chip-text">发送「{item.text}」</span>
            ) : (
              <span className="walkthrough-chip-text">打开确认框</span>
            )}
          </button>
        ))}
      </div>
    </section>
  );
}
