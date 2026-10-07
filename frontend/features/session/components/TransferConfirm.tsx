"use client";

type Props = {
  open: boolean;
  busy: boolean;
  onCancel: () => void;
  onConfirm: () => void;
};

export function TransferConfirm({ open, busy, onCancel, onConfirm }: Props) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="presentation" onClick={onCancel}>
      <div
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="transfer-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="transfer-title">要转接人工客服吗？</h2>
        <p>转接后将结束当前数字人咨询，由人工同事继续协助；本会话不能再发送消息。</p>
        <div className="chip-row">
          <button type="button" className="btn ghost" disabled={busy} onClick={onCancel}>
            取消
          </button>
          <button type="button" className="btn danger" disabled={busy} onClick={onConfirm}>
            确认
          </button>
        </div>
      </div>
    </div>
  );
}
