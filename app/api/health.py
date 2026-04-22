"""Health endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from ..config import get_settings

router = APIRouter()


@router.get("/health")
def health() -> dict:
    s = get_settings()
    return {"status": "ok", "app": s.app_name, "llm_mode": s.llm_mode}
