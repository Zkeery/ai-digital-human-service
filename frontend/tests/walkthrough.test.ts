import { describe, expect, it } from "vitest";

import {
  PRODUCT_WALKTHROUGH_ITEMS,
  isWalkthroughTransfer,
  walkthroughSendText,
} from "../features/session/walkthrough";

describe("product walkthrough shortcuts", () => {
  it("covers checklist phrases without real card numbers beyond fake sample", () => {
    const ids = PRODUCT_WALKTHROUGH_ITEMS.map((i) => i.checklist).sort();
    expect(ids).toEqual([2, 3, 4, 6, 8]);
    const bind = PRODUCT_WALKTHROUGH_ITEMS.find((i) => i.id === "bind-card");
    expect(bind?.text).toContain("622202");
    expect(bind?.text).not.toMatch(/\b\d{16,19}\b.*真/);
  });

  it("routes transfer separately from send text", () => {
    const transfer = PRODUCT_WALKTHROUGH_ITEMS.find((i) => i.id === "transfer");
    expect(transfer && isWalkthroughTransfer(transfer)).toBe(true);
    expect(transfer && walkthroughSendText(transfer)).toBe("");
    const balance = PRODUCT_WALKTHROUGH_ITEMS.find((i) => i.id === "balance");
    expect(balance && walkthroughSendText(balance)).toBe("查余额");
  });
});
