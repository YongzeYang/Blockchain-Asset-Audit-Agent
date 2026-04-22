"""Load skill YAML files from disk."""
from __future__ import annotations

import logging
from pathlib import Path

import yaml

from ..schemas.skills import SkillDefinition

logger = logging.getLogger(__name__)


def load_skills_from_dir(dir_path: str | Path) -> list[SkillDefinition]:
    p = Path(dir_path)
    skills: list[SkillDefinition] = []
    if not p.exists():
        logger.warning("Skills directory %s does not exist", p)
        return skills
    for f in sorted(p.glob("*.yaml")) + sorted(p.glob("*.yml")):
        try:
            with f.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
            skills.append(SkillDefinition.model_validate(data))
            logger.info("Loaded skill %s from %s", data.get("id"), f.name)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load skill from %s: %s", f, exc)
    return skills


def skill_to_yaml(skill: SkillDefinition) -> str:
    return yaml.safe_dump(
        skill.model_dump(mode="json"),
        sort_keys=False,
        allow_unicode=True,
    )
