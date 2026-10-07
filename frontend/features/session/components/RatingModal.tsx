"use client";

type Props = {
  open: boolean;
  busy: boolean;
  score: number;
  onScoreChange: (score: number) => void;
  onSkip: () => void;
  onSubmit: () => void;
};

export function RatingModal({ open, busy, score, onScoreChange, onSkip, onSubmit }: Props) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="presentation" onClick={onSkip}>
      <div
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="rating-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="rating-title">本次咨询打个分？</h2>
        <p>金融咨询已结束。选个星级告诉我们体验如何，也可以跳过。</p>
        <div className="rating-stars" role="group" aria-label="评分星级">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              className={`btn ghost rating-star ${score === n ? "active-star" : ""}`}
              disabled={busy}
              onClick={() => onScoreChange(n)}
              aria-label={`${n} 星`}
              aria-pressed={score === n}
            >
              {n}★
            </button>
          ))}
        </div>
        <div className="rating-actions">
          <button type="button" className="btn ghost" disabled={busy} onClick={onSkip}>
            跳过
          </button>
          <button type="button" className="btn" disabled={busy} onClick={onSubmit}>
            提交评价
          </button>
        </div>
      </div>
    </div>
  );
}
