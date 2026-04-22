"""Skill endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..agent import orchestrator
from ..schemas.skills import SkillDefinition, SkillDraftRequest, SkillDraftResponse
from ..skills.registry import get_registry
from .auth import require_invite_code

router = APIRouter(prefix="/v1/skills")


@router.get("")
def list_skills() -> list[SkillDefinition]:
    return get_registry().list()


@router.get("/{skill_id}")
def get_skill(skill_id: str) -> SkillDefinition:
    return get_registry().get(skill_id)  # UnknownSkillError handled globally


@router.post("/generate", response_model=SkillDraftResponse, dependencies=[Depends(require_invite_code)])
def generate_skill(req: SkillDraftRequest) -> SkillDraftResponse:
    return orchestrator.run_skill_draft(req)


@router.post("/save", dependencies=[Depends(require_invite_code)])
def save_skill(skill: SkillDefinition) -> dict:
    get_registry().register(skill, persist_yaml=True)
    return {
        "id": skill.id,
        "name": skill.name,
        "version": skill.version,
        "enabled": skill.enabled,
        "saved": True,
    }
