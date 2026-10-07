/** 产品走查清单对应的验收快捷句（仅验收模式展示）。 */

export type WalkthroughItem = {
  id: string;
  checklist: number;
  label: string;
  text: string;
  /** transfer = 只打开转人工确认，不发送 */
  kind?: "send" | "transfer";
};

export const PRODUCT_WALKTHROUGH_ITEMS: WalkthroughItem[] = [
  {
    id: "balance",
    checklist: 2,
    label: "#2 查余额",
    text: "查余额",
    kind: "send",
  },
  {
    id: "credit",
    checklist: 3,
    label: "#3 办信用卡",
    text: "办信用卡",
    kind: "send",
  },
  {
    id: "return",
    checklist: 4,
    label: "#4 怎么退货",
    text: "怎么退货",
    kind: "send",
  },
  {
    id: "bind-card",
    checklist: 8,
    label: "#8 假卡号绑卡",
    text: "6222021234567890123 怎么绑卡",
    kind: "send",
  },
  {
    id: "transfer",
    checklist: 6,
    label: "#6 转人工",
    text: "转人工",
    kind: "transfer",
  },
];

export function walkthroughSendText(item: WalkthroughItem): string {
  return item.kind === "transfer" ? "" : item.text.trim();
}

export function isWalkthroughTransfer(item: WalkthroughItem): boolean {
  return item.kind === "transfer";
}
