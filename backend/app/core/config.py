from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_host: str = "127.0.0.1"
    app_port: int = 8050
    data_dir: str = str(PROJECT_ROOT / "data")
    database_url: str = ""

    pilot_entry_id: str = "entry_pilot_001"
    agent_enabled: bool = False
    rag_enabled: bool = False
    rag_timeout_seconds: float = 0.5

    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_mock: bool = True
    llm_timeout_seconds: float = 8.0
    monthly_budget_cny: float = 500.0
    room_active_limit: int = 30
    sync_hold_ms: int = 2000
    history_limit: int = 10

    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        db_path = Path(self.data_dir) / "app.db"
        return f"sqlite:///{db_path}"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    return settings
