import { describe, expect, it, vi } from "vitest";

import { copyTextToClipboard } from "../lib/clipboard";

describe("copyTextToClipboard", () => {
  it("rejects empty text", async () => {
    await expect(copyTextToClipboard("   ")).resolves.toBe(false);
  });

  it("uses navigator.clipboard when available", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } });
    await expect(copyTextToClipboard("客服回复内容")).resolves.toBe(true);
    expect(writeText).toHaveBeenCalledWith("客服回复内容");
    vi.unstubAllGlobals();
  });
});
