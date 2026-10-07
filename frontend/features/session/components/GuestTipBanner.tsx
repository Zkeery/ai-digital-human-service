"use client";

type Props = {
  onDismiss: () => void;
};

export function GuestTipBanner({ onDismiss }: Props) {
  return (
    <div className="guest-tip" role="note">
      <p className="guest-tip-text">
        用文字说明问题即可（如查余额、办信用卡）。查账、转账、改密需本人到官方 App 办理；需要同事协助请点「转人工」。
      </p>
      <button type="button" className="guest-tip-dismiss" onClick={onDismiss}>
        知道了
      </button>
    </div>
  );
}
