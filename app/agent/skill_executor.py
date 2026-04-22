"""Generic skill executor: dispatch payload to the right orchestrator entry point."""
from __future__ import annotations

from typing import Any

from ..schemas.audit import AuditRunRequest
from ..schemas.skills import SkillDraftRequest
from ..skills.registry import get_registry
from . import orchestrator


class SkillDispatchError(Exception):
    pass


def execute(skill_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    skill = get_registry().get(skill_id)

    if skill.output_schema == "AuditReport":
        payload = {**payload, "skill_id": skill_id}
        req = AuditRunRequest.model_validate(payload)
        resp = orchestrator.run_audit(req)
        return resp.model_dump(mode="json")

    if skill.output_schema == "SkillDefinition":
        req = SkillDraftRequest.model_validate(payload)
        resp = orchestrator.run_skill_draft(req)
        return resp.model_dump(mode="json")

    raise SkillDispatchError(
        f"No executor wired for skill '{skill_id}' with output schema '{skill.output_schema}'."
    )
