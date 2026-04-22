"""Skill repository (SQLite)."""
from __future__ import annotations

from typing import Any

from ..schemas.skills import SkillDefinition
from ..utils.json_utils import dumps, loads
from ..utils.time_utils import utcnow_iso
from .db import get_conn


def upsert_skill(skill: SkillDefinition) -> None:
    body = skill.model_dump(mode="json")
    now = utcnow_iso()
    with get_conn() as conn:
        existing = conn.execute("SELECT id FROM skills WHERE id = ?", (skill.id,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE skills SET version=?, enabled=?, body_json=?, updated_at=? WHERE id=?",
                (skill.version, 1 if skill.enabled else 0, dumps(body), now, skill.id),
            )
        else:
            conn.execute(
                "INSERT INTO skills (id, version, enabled, body_json, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (skill.id, skill.version, 1 if skill.enabled else 0, dumps(body), now, now),
            )


def get_skill(skill_id: str) -> SkillDefinition | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
    if not row:
        return None
    body = loads(row["body_json"]) or {}
    return SkillDefinition.model_validate(body)


def list_skills() -> list[SkillDefinition]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM skills ORDER BY id ASC").fetchall()
    return [SkillDefinition.model_validate(loads(r["body_json"]) or {}) for r in rows]
