"""In-memory skill registry."""
from __future__ import annotations

import logging
import threading
from pathlib import Path

from ..config import get_settings
from ..schemas.skills import SkillDefinition
from ..storage import skill_repository
from .loader import load_skills_from_dir, skill_to_yaml

logger = logging.getLogger(__name__)


class UnknownSkillError(Exception):
    pass


class SkillRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._skills: dict[str, SkillDefinition] = {}

    def load_all(self) -> None:
        settings = get_settings()
        with self._lock:
            self._skills.clear()
            for s in load_skills_from_dir(settings.skills_dir):
                self._skills[s.id] = s
            # DB-saved skills override file-based ones (so user-saved drafts win).
            try:
                for s in skill_repository.list_skills():
                    self._skills[s.id] = s
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not load skills from DB: %s", exc)

    def get(self, skill_id: str) -> SkillDefinition:
        with self._lock:
            if skill_id not in self._skills:
                raise UnknownSkillError(f"Unknown skill: {skill_id}")
            return self._skills[skill_id]

    def list(self) -> list[SkillDefinition]:
        with self._lock:
            return list(self._skills.values())

    def register(self, skill: SkillDefinition, persist_yaml: bool = True) -> None:
        with self._lock:
            self._skills[skill.id] = skill
        skill_repository.upsert_skill(skill)
        if persist_yaml:
            try:
                settings = get_settings()
                target = Path(settings.skills_dir) / f"{skill.id}.yaml"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(skill_to_yaml(skill), encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to persist skill YAML: %s", exc)


_registry: SkillRegistry | None = None
_registry_lock = threading.Lock()


def get_registry() -> SkillRegistry:
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = SkillRegistry()
                _registry.load_all()
    return _registry


def reset_registry_for_tests() -> None:
    global _registry
    _registry = None
