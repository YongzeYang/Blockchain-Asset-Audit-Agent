"""Common schemas shared across the API."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TimeRange(BaseModel):
    model_config = ConfigDict(extra="ignore")
    start: datetime | None = None
    end: datetime | None = None


class EvidenceRef(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source_type: str = Field(description="e.g. transaction, balance, ledger, knowledge")
    reference: str = Field(description="tx_hash, entry_id, doc id, etc.")
    detail: str | None = None


class ToolCallLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    result: Any | None = None
    created_at: datetime
    error: str | None = None


class RunSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    run_id: str
    skill_id: str
    status: str
    created_at: datetime
    updated_at: datetime


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    error: str
    detail: str | None = None
