import type { EntryStatsView, StatsView } from "@/lib/api/session";

/** 汇总行文案（验收面板用）。 */
export function formatStatsSummary(stats: StatsView): string {
  return (
    `会话 ${stats.sessions_total}（进行中 ${stats.sessions_active}／已转人工 ${stats.sessions_transferred}）` +
    ` · Agent 使用 ${stats.agent_used}／跳过 ${stats.agent_skipped}` +
    ` · 评价 ${stats.ratings}`
  );
}

export function formatEntryStatsLine(row: EntryStatsView): string {
  return (
    `${row.label}：会话 ${row.sessions}` +
    ` · 转人工 ${row.transferred}` +
    ` · Agent ${row.agent_used}` +
    ` · 跳过 ${row.agent_skipped}`
  );
}
