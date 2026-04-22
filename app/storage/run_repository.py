"""Run + tool_call repository."""
from __future__ import annotations

from typing import Any

from ..schemas.common import ToolCallLog
from ..utils.json_utils import dumps, loads
from ..utils.time_utils import parse_dt, utcnow_iso
from .db import get_conn


def create_run(
    run_id: str,
    skill_id: str,
    status: str,
    input_payload: dict[str, Any],
) -> None:
    now = utcnow_iso()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO runs (id, skill_id, status, input_json, output_json, error_text, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, NULL, NULL, ?, ?)",
            (run_id, skill_id, status, dumps(input_payload), now, now),
        )


def update_run(
    run_id: str,
    *,
    status: str | None = None,
    output_payload: dict[str, Any] | None = None,
    error_text: str | None = None,
) -> None:
    fields: list[str] = []
    values: list[Any] = []
    if status is not None:
        fields.append("status = ?")
        values.append(status)
    if output_payload is not None:
        fields.append("output_json = ?")
        values.append(dumps(output_payload))
    if error_text is not None:
        fields.append("error_text = ?")
        values.append(error_text)
    fields.append("updated_at = ?")
    values.append(utcnow_iso())
    values.append(run_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE runs SET {', '.join(fields)} WHERE id = ?", values)


def add_tool_call(call: ToolCallLog, run_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO tool_calls (id, run_id, tool_name, args_json, result_json, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                call.id,
                run_id,
                call.tool_name,
                dumps(call.args),
                dumps({"result": call.result, "error": call.error}),
                call.created_at.isoformat() if hasattr(call.created_at, "isoformat") else str(call.created_at),
            ),
        )


def _row_to_run(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "skill_id": row["skill_id"],
        "status": row["status"],
        "input_payload": loads(row["input_json"]) or {},
        "output_payload": loads(row["output_json"]),
        "error_text": row["error_text"],
        "created_at": parse_dt(row["created_at"]),
        "updated_at": parse_dt(row["updated_at"]),
    }


def get_run(run_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return _row_to_run(row) if row else None


def list_runs(limit: int = 50) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [_row_to_run(r) for r in rows]


def list_tool_calls_for_run(run_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tool_calls WHERE run_id = ? ORDER BY created_at ASC",
            (run_id,),
        ).fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        result_blob = loads(r["result_json"]) or {}
        out.append(
            {
                "id": r["id"],
                "tool_name": r["tool_name"],
                "args": loads(r["args_json"]) or {},
                "result": result_blob.get("result"),
                "error": result_blob.get("error"),
                "created_at": parse_dt(r["created_at"]),
            }
        )
    return out
