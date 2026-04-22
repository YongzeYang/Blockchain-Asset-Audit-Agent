"""Skill-related schemas."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SkillDefinition(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    system_instruction: str
    allowed_tools: list[str] = Field(default_factory=list)
    output_schema: str
    tags: list[str] = Field(default_factory=list)
    risk_rules: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    enabled: bool = True
    version: str = "0.1.0"


class SkillDraftRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    skill_name: str
    domain: str | None = None
    expert_text: str
    notes: str | None = None


class SkillDraftResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    draft: SkillDefinition
    yaml_preview: str
