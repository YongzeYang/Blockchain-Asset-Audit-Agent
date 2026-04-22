"""Application configuration loaded from environment variables."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILES = (
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / ".env.local",
    PROJECT_ROOT / ".env.vertex.local",
)


class Settings(BaseModel):
    app_name: str = Field(default="ai-agent-mvp")
    app_env: str = Field(default="dev")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8042)
    app_db_path: str = Field(default="./app_data/agent.db")

    # LLM
    llm_mode: str = Field(default="mock")  # "mock" | "vertex"
    gemini_model: str = Field(default="gemini-2.5-flash")

    # Vertex AI
    google_cloud_project: str = Field(default="")
    google_cloud_location: str = Field(default="global")
    google_genai_use_vertexai: bool = Field(default=True)

    # Logging
    log_level: str = Field(default="INFO")

    # Audit heuristics
    large_tx_threshold: float = Field(default=100000.0)
    default_skill_id: str = Field(default="asset_audit_basic")

    # Project paths
    skills_dir: str = Field(default="./skills")
    knowledge_dir: str = Field(default="./knowledge")
    address_book_path: str = Field(default="./data/address_book.json")

    # CORS
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5215",
            "http://127.0.0.1:5215",
        ]
    )

    @property
    def db_path_resolved(self) -> Path:
        p = Path(self.app_db_path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        return p


def _bool_env(name: str, default: bool) -> bool:
    raw = _env_values().get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _float_env(name: str, default: float) -> float:
    raw = _env_values().get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _int_env(name: str, default: int) -> int:
    raw = _env_values().get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _parse_csv(raw: str | None, default: list[str]) -> list[str]:
    if raw is None:
        return list(default)
    items = [item.strip() for item in raw.split(",") if item.strip()]
    return items or list(default)


@lru_cache(maxsize=1)
def _env_values() -> dict[str, str]:
    merged: dict[str, str] = {}
    for file_path in ENV_FILES:
        if not file_path.exists():
            continue
        for key, value in dotenv_values(file_path).items():
            if value is not None:
                merged[key] = value
    for key, value in os.environ.items():
        merged[key] = value
    return merged


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    env = _env_values()
    return Settings(
        app_name=env.get("APP_NAME", "ai-agent-mvp"),
        app_env=env.get("APP_ENV", "dev"),
        app_host=env.get("APP_HOST", "0.0.0.0"),
        app_port=_int_env("APP_PORT", 8042),
        app_db_path=env.get("APP_DB_PATH", "./app_data/agent.db"),
        llm_mode=env.get("LLM_MODE", "mock").lower(),
        gemini_model=env.get("GEMINI_MODEL", "gemini-2.5-flash"),
        google_cloud_project=env.get("GOOGLE_CLOUD_PROJECT", ""),
        google_cloud_location=env.get("GOOGLE_CLOUD_LOCATION", "global"),
        google_genai_use_vertexai=_bool_env("GOOGLE_GENAI_USE_VERTEXAI", True),
        log_level=env.get("LOG_LEVEL", "INFO"),
        large_tx_threshold=_float_env("LARGE_TX_THRESHOLD", 100000.0),
        default_skill_id=env.get("DEFAULT_SKILL_ID", "asset_audit_basic"),
        skills_dir=env.get("SKILLS_DIR", "./skills"),
        knowledge_dir=env.get("KNOWLEDGE_DIR", "./knowledge"),
        address_book_path=env.get("ADDRESS_BOOK_PATH", "./data/address_book.json"),
        cors_origins=_parse_csv(
            env.get("CORS_ORIGINS"),
            default=["http://localhost:5215", "http://127.0.0.1:5215"],
        ),
    )


def reset_settings_cache() -> None:
    _env_values.cache_clear()
    get_settings.cache_clear()
