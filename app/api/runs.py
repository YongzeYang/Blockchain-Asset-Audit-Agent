"""Run history endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas.common import RunSummary
from ..schemas.runs import RunDetailResponse
from ..storage import run_repository

router = APIRouter(prefix="/v1/runs")


@router.get("")
def list_runs(limit: int = 50) -> list[RunSummary]:
    rows = run_repository.list_runs(limit=limit)
    return [
        RunSummary(
            run_id=r["id"],
            skill_id=r["skill_id"] or "",
            status=r["status"] or "",
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in rows
    ]


@router.get("/{run_id}", response_model=RunDetailResponse)
def get_run(run_id: str) -> RunDetailResponse:
    row = run_repository.get_run(run_id)
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
    tool_calls = run_repository.list_tool_calls_for_run(run_id)
    return RunDetailResponse(
        run_id=row["id"],
        status=row["status"] or "",
        skill_id=row["skill_id"] or "",
        input_payload=row["input_payload"] or {},
        output_payload=row["output_payload"],
        tool_calls=[
            {
                "id": c["id"],
                "tool_name": c["tool_name"],
                "args": c["args"],
                "result": c["result"],
                "error": c["error"],
                "created_at": c["created_at"],
            }
            for c in tool_calls
        ],
        error=row["error_text"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
