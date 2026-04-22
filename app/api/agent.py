"""Generic agent run endpoint."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..agent.skill_executor import SkillDispatchError, execute
from .auth import require_invite_code

router = APIRouter(prefix="/v1/agent")


class AgentRunRequest(BaseModel):
    skill_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


@router.post("/run", dependencies=[Depends(require_invite_code)])
def agent_run(req: AgentRunRequest) -> dict:
    try:
        return execute(req.skill_id, req.payload)
    except SkillDispatchError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
