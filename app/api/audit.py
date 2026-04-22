"""Audit endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..agent import orchestrator
from ..schemas.audit import AuditRunRequest, AuditRunResponse
from .auth import require_invite_code

router = APIRouter(prefix="/v1/audit")


@router.post("/run", response_model=AuditRunResponse, dependencies=[Depends(require_invite_code)])
def run_audit(req: AuditRunRequest) -> AuditRunResponse:
    return orchestrator.run_audit(req)
