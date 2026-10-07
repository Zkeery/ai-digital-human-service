"use client";

import type { Banner } from "../bannerView";
import { bannerClassName } from "../bannerView";

type Props = {
  banner: Banner;
  onDismiss: () => void;
  onRetry?: () => void;
};

export function StatusBanner({ banner, onDismiss, onRetry }: Props) {
  return (
    <div className={bannerClassName(banner)} role="status">
      <p className="banner-text">{banner.text}</p>
      <div className="banner-actions">
        {banner.retry && onRetry ? (
          <button type="button" className="banner-retry" onClick={onRetry}>
            重试
          </button>
        ) : null}
        <button type="button" className="banner-close" onClick={onDismiss} aria-label="关闭提示">
          关闭
        </button>
      </div>
    </div>
  );
}
