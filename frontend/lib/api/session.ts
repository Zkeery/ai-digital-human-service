import { apiJson } from "./client";

export type EntryView = {
  id: string;
  label: string;
  welcome_text: string;
  theme: string;
  accent: string;
  logo_url: string;
  agent_enabled: boolean;
};

export type ConfigView = {
  pilot_entry_id: string;
  agent_enabled: boolean;
  rag_enabled: boolean;
  llm_mock: boolean;
  monthly_budget_cny: number;
  room_active_limit: number;
  sync_hold_ms: number;
  entries: EntryView[];
};

export type SessionCreated = {
  session_id: string;
  entry_id: string;
  status: string;
};

export type QuickReply = {
  label: string;
  text: string;
};

export type MessageReply = {
  session_id: string;
  spoken_text: string;
  action_intent: string;
  graphic_template_ref: string;
  agent_used: boolean;
  suggest_transfer_human: boolean;
  source: string;
  push_ready: boolean;
  sync_hold_ms: number;
  quick_replies?: QuickReply[];
};

export type SessionSnapshot = SessionCreated & {
  last_reply?: MessageReply | null;
};

export type HistoryItem = {
  role: string;
  text: string;
  created_at?: string;
  kind?: "welcome" | "chat";
};

export type SessionEvent = {
  id: number;
  session_id: string;
  event_key: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type EntryStatsView = {
  entry_id: string;
  label: string;
  sessions: number;
  transferred: number;
  agent_used: number;
  agent_skipped: number;
};

export type StatsView = {
  sessions_total: number;
  sessions_active: number;
  sessions_transferred: number;
  transfer_events: number;
  agent_used: number;
  agent_skipped: number;
  messages_replied: number;
  ratings: number;
  by_entry: EntryStatsView[];
};

export const api = {
  getConfig: () => apiJson<ConfigView>("/api/v1/config"),
  putConfig: (body: {
    agent_enabled?: boolean;
    rag_enabled?: boolean;
    pilot_entry_id?: string;
  }) => apiJson<ConfigView>("/api/v1/config", { method: "PUT", body: JSON.stringify(body) }),
  createSession: (entry_id: string) =>
    apiJson<SessionCreated>("/api/v1/sessions", {
      method: "POST",
      body: JSON.stringify({ entry_id }),
    }),
  getSession: (sessionId: string) =>
    apiJson<SessionSnapshot>(`/api/v1/sessions/${sessionId}`),
  sendMessage: (sessionId: string, text: string) =>
    apiJson<MessageReply>(`/api/v1/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  guide: (sessionId: string) =>
    apiJson<{ ok?: boolean; spoken_text?: string }>(`/api/v1/sessions/${sessionId}/guide`, {
      method: "POST",
      body: "{}",
    }),
  initDh: (sessionId: string, d_profile_key: string) =>
    apiJson<{
      room_id?: string;
      d_profile_key?: string;
      reused?: boolean;
      welcome_command_id?: number | null;
      sync_hold_ms?: number;
    }>(`/api/v1/sessions/${sessionId}/digital-human/init`, {
      method: "POST",
      body: JSON.stringify({ d_profile_key }),
    }),
  push: (sessionId: string) =>
    apiJson<{ command_db_id: number; status: string; kind: string }>(
      `/api/v1/sessions/${sessionId}/digital-human/push`,
      { method: "POST", body: "{}" },
    ),
  streamStarted: (sessionId: string, command_db_id: number) =>
    apiJson<Record<string, unknown>>(
      `/api/v1/sessions/${sessionId}/digital-human/stream-started`,
      { method: "POST", body: JSON.stringify({ command_db_id }) },
    ),
  checkSync: (sessionId: string) =>
    apiJson<{ fallback: boolean; reason: string; hold_ms?: number }>(
      `/api/v1/sessions/${sessionId}/digital-human/check-sync`,
      { method: "POST", body: "{}" },
    ),
  fallback: (sessionId: string) =>
    apiJson<{ ok: boolean }>(`/api/v1/sessions/${sessionId}/fallback`, {
      method: "POST",
      body: "{}",
    }),
  transfer: (sessionId: string) =>
    apiJson<{ session_id: string; status: string }>(
      `/api/v1/sessions/${sessionId}/transfer`,
      { method: "POST", body: "{}" },
    ),
  rating: (sessionId: string, score: number, comment = "") =>
    apiJson<Record<string, unknown>>(`/api/v1/sessions/${sessionId}/rating`, {
      method: "POST",
      body: JSON.stringify({ rating_type: "digital_human", score, comment }),
    }),
  history: (sessionId: string) =>
    apiJson<{ items: HistoryItem[] }>(`/api/v1/sessions/${sessionId}/history`),
  events: (sessionId: string) =>
    apiJson<SessionEvent[]>(`/api/v1/sessions/${sessionId}/events`),
  stats: () => apiJson<StatsView>("/api/v1/stats"),
  themes: () => apiJson<{ themes: { id: string; label: string }[] }>("/api/v1/themes"),
  special: (sessionId: string, command_id: string) =>
    apiJson<Record<string, unknown>>(`/api/v1/sessions/${sessionId}/digital-human/special`, {
      method: "POST",
      body: JSON.stringify({ command_id }),
    }),
};
