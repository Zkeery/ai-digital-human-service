from __future__ import annotations

from pydantic import BaseModel, Field


class EntryView(BaseModel):
    id: str
    label: str
    welcome_text: str
    theme: str = "default"
    accent: str = "#0f766e"
    logo_url: str = ""
    agent_enabled: bool = False


class ConfigView(BaseModel):
    pilot_entry_id: str
    agent_enabled: bool
    rag_enabled: bool = False
    llm_mock: bool
    monthly_budget_cny: float
    room_active_limit: int
    sync_hold_ms: int
    entries: list[EntryView] = Field(default_factory=list)


class ConfigUpdate(BaseModel):
    agent_enabled: bool | None = None
    rag_enabled: bool | None = None
    pilot_entry_id: str | None = None


class CreateSessionRequest(BaseModel):
    entry_id: str = Field(min_length=1, max_length=128)


class CreateSessionResponse(BaseModel):
    session_id: str
    entry_id: str
    status: str


class MessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class QuickReply(BaseModel):
    label: str
    text: str


class MessageResponse(BaseModel):
    session_id: str
    spoken_text: str
    action_intent: str
    graphic_template_ref: str
    agent_used: bool
    suggest_transfer_human: bool
    source: str
    push_ready: bool = False
    sync_hold_ms: int = 2000
    quick_replies: list[QuickReply] = Field(default_factory=list)


class EventItem(BaseModel):
    id: int
    session_id: str
    event_key: str
    payload: dict
    created_at: str


class SessionStatusResponse(BaseModel):
    session_id: str
    entry_id: str
    status: str


class SessionSnapshotResponse(SessionStatusResponse):
    """刷新恢复用：active 时可带回上次回复与当前快捷选项。"""

    last_reply: MessageResponse | None = None


class InitDigitalHumanRequest(BaseModel):
    d_profile_key: str = Field(min_length=3, max_length=8)


class StreamStartedRequest(BaseModel):
    command_db_id: int


class RatingRequest(BaseModel):
    rating_type: str
    score: int = Field(ge=1, le=5)
    comment: str | None = None


class SpecialCommandRequest(BaseModel):
    command_id: str
    spoken_text: str | None = None


class ComposeReplyRequest(BaseModel):
    session_id: str
    user_utterance: str = Field(min_length=1, max_length=2000)
    faq_hit: dict | None = None
    last_visible_messages: list[str] = Field(default_factory=list)
    allow_tools: list[str] = Field(default_factory=list)


class EntryStatsView(BaseModel):
    entry_id: str
    label: str
    sessions: int
    transferred: int
    agent_used: int
    agent_skipped: int


class StatsView(BaseModel):
    """近程 B1：本地库汇总，仅验收模式展示。"""

    sessions_total: int
    sessions_active: int
    sessions_transferred: int
    transfer_events: int
    agent_used: int
    agent_skipped: int
    messages_replied: int
    ratings: int
    by_entry: list[EntryStatsView] = Field(default_factory=list)
