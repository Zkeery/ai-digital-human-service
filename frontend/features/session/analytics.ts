/** PRD §11 埋点骨架：前端本地记录，不改后端协议。 */

export type DhEventKey =
  | "dh_guide_show"
  | "dh_init_success"
  | "dh_init_fail"
  | "dh_sync_fallback_2s"
  | "dh_agent_used"
  | "dh_agent_skipped"
  | "dh_transfer_human"
  | "dh_rate"
  | "dh_entry_selected"
  | "dh_rag_hit"
  | "dh_rag_miss"
  | "dh_rag_skip"
  | "dh_local_speech";

export type DhEvent = {
  key: DhEventKey;
  at: string;
  sessionId: string | null;
  detail?: string;
};

const MAX_EVENTS = 40;

let buffer: DhEvent[] = [];
const listeners = new Set<() => void>();

export function dhEventLabel(key: DhEventKey): string {
  switch (key) {
    case "dh_guide_show":
      return "引导展示";
    case "dh_init_success":
      return "初始化成功";
    case "dh_init_fail":
      return "初始化失败";
    case "dh_sync_fallback_2s":
      return "2s 同步降级";
    case "dh_agent_used":
      return "使用了 Agent";
    case "dh_agent_skipped":
      return "未走 Agent";
    case "dh_transfer_human":
      return "转人工";
    case "dh_rate":
      return "提交评价";
    case "dh_entry_selected":
      return "选用入口";
    case "dh_rag_hit":
      return "RAG 命中";
    case "dh_rag_miss":
      return "RAG 未命中";
    case "dh_rag_skip":
      return "RAG 跳过";
    case "dh_local_speech":
      return "本地口播";
    default:
      return key;
  }
}

export function trackDh(
  key: DhEventKey,
  opts?: { sessionId?: string | null; detail?: string },
): DhEvent {
  const ev: DhEvent = {
    key,
    at: new Date().toISOString(),
    sessionId: opts?.sessionId ?? null,
    detail: opts?.detail,
  };
  buffer = [ev, ...buffer].slice(0, MAX_EVENTS);
  listeners.forEach((fn) => fn());
  return ev;
}

export function listDhEvents(): DhEvent[] {
  return buffer.slice();
}

export function clearDhEvents(): void {
  buffer = [];
  listeners.forEach((fn) => fn());
}

export function subscribeDhEvents(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** 测试用：重置内存缓冲。 */
export function resetDhEventsForTests(): void {
  buffer = [];
  listeners.clear();
}
