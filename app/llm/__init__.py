"""LLM client factory."""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from ..config import Settings, get_settings
from .base import LLMClient
from .mock_client import MockLLMClient

logger = logging.getLogger(__name__)


class LLMNotConfiguredError(Exception):
    pass


def has_adc_credentials() -> bool:
    try:
        import google.auth

        google.auth.default()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.debug("ADC credentials not available: %s", exc)
        return False


def detect_adc_project_id() -> str | None:
    try:
        import google.auth

        _, project_id = google.auth.default()
        return project_id or None
    except Exception as exc:  # noqa: BLE001
        logger.debug("ADC project id not available: %s", exc)
        return None


def detect_gcloud_project_id() -> str | None:
    candidates = []
    if gcloud_path := shutil.which("gcloud"):
        candidates.append(gcloud_path)
    snap_gcloud = Path("/snap/bin/gcloud")
    if snap_gcloud.exists():
        candidates.append(str(snap_gcloud))
    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "config", "get-value", "project"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to query gcloud project from %s: %s", candidate, exc)
            continue
        value = (result.stdout or "").strip()
        if result.returncode == 0 and value and value != "(unset)":
            return value
    return None


def resolve_vertex_project_id(explicit_project: str | None = None) -> str | None:
    if explicit_project and explicit_project.strip():
        return explicit_project.strip()
    return detect_adc_project_id() or detect_gcloud_project_id()


def get_llm_client(settings: Settings | None = None) -> LLMClient:
    s = settings or get_settings()
    mode = (s.llm_mode or "mock").lower()
    if mode == "mock":
        return MockLLMClient()
    if mode == "vertex":
        if not s.google_genai_use_vertexai:
            raise LLMNotConfiguredError(
                "This project only supports Gemini through Vertex AI. Set GOOGLE_GENAI_USE_VERTEXAI=True."
            )
        if not has_adc_credentials():
            raise LLMNotConfiguredError(
                "Vertex AI requires Application Default Credentials (ADC). Run `gcloud auth application-default login` first."
            )
        project_id = resolve_vertex_project_id(s.google_cloud_project)
        if not project_id:
            raise LLMNotConfiguredError(
                "Vertex AI requires a Google Cloud project. Set GOOGLE_CLOUD_PROJECT or run `gcloud config set project <PROJECT_ID>`."
            )
        from .gemini_client import GeminiVertexClient

        return GeminiVertexClient(
            project=project_id,
            location=s.google_cloud_location,
            model=s.gemini_model,
            use_vertex=s.google_genai_use_vertexai,
        )
    raise LLMNotConfiguredError(f"Unknown LLM_MODE: {mode}")
