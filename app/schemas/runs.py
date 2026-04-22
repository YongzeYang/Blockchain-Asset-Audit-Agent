"""Run schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .common import ToolCallLog


class RunDetailResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    run_id: str
    status: str
    skill_id: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] | None = None
    tool_calls: list[ToolCallLog] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime
    updated_at: datetime
