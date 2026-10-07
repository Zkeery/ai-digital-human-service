import { describe, expect, it } from "vitest";

import {
  normalizeQuickReplies,
  resolveDisplayedQuickReplies,
  shouldShowQuickReplies,
} from "../features/session/quickReplies";

describe("quick replies", () => {
  it("normalizes and caps at 5", () => {
    expect(normalizeQuickReplies(null)).toEqual([]);
    expect(
      normalizeQuickReplies([
        { label: "尺码不合适", text: "尺码不合适" },
        { label: " ", text: "" },
        { label: "确认退货" },
      ]),
    ).toEqual([
      { label: "尺码不合适", text: "尺码不合适" },
      { label: "确认退货", text: "确认退货" },
    ]);
    const many = Array.from({ length: 8 }, (_, i) => ({
      label: `选项${i + 1}`,
      text: `选项${i + 1}`,
    }));
    expect(normalizeQuickReplies(many)).toHaveLength(5);
  });

  it("drops transfer chips that duplicate the toolbar", () => {
    expect(
      normalizeQuickReplies([
        { label: "查流水", text: "查流水" },
        { label: "转人工", text: "转人工" },
        { label: "人工客服", text: "人工客服" },
      ]),
    ).toEqual([{ label: "查流水", text: "查流水" }]);
  });

  it("hides when transferred or empty", () => {
    expect(shouldShowQuickReplies("transferred", [{ label: "a", text: "a" }])).toBe(false);
    expect(shouldShowQuickReplies("active", [])).toBe(false);
    expect(shouldShowQuickReplies("active", [{ label: "想换货", text: "想换货" }])).toBe(true);
  });

  it("shows only backend keyword chips, no starter wall", () => {
    const empty = resolveDisplayedQuickReplies({
      status: "active",
      canChat: true,
      backendReplies: [],
    });
    expect(empty).toEqual({ primary: [], more: [], isStarter: false });

    const backend = [
      { label: "查积分", text: "查积分" },
      { label: "怎么用", text: "怎么用" },
    ];
    expect(
      resolveDisplayedQuickReplies({ status: "active", canChat: true, backendReplies: backend }),
    ).toEqual({ primary: backend, more: [], isStarter: false });
  });
});
