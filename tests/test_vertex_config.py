from __future__ import annotations

import pytest

import app.llm as llm
from app.config import Settings


def test_resolve_vertex_project_id_prefers_explicit(monkeypatch):
    monkeypatch.setattr(llm, "detect_adc_project_id", lambda: "adc-project")
    monkeypatch.setattr(llm, "detect_gcloud_project_id", lambda: "gcloud-project")

    assert llm.resolve_vertex_project_id("explicit-project") == "explicit-project"


def test_resolve_vertex_project_id_falls_back_to_detected_sources(monkeypatch):
    monkeypatch.setattr(llm, "detect_adc_project_id", lambda: None)
    monkeypatch.setattr(llm, "detect_gcloud_project_id", lambda: "gcloud-project")

    assert llm.resolve_vertex_project_id(None) == "gcloud-project"


def test_get_llm_client_vertex_requires_adc(monkeypatch):
    settings = Settings(llm_mode="vertex", google_cloud_project="blockchain-asset-audit-agent")
    monkeypatch.setattr(llm, "has_adc_credentials", lambda: False)

    with pytest.raises(llm.LLMNotConfiguredError, match="Application Default Credentials"):
        llm.get_llm_client(settings)


def test_get_llm_client_vertex_requires_vertex_transport():
    settings = Settings(
        llm_mode="vertex",
        google_cloud_project="blockchain-asset-audit-agent",
        google_genai_use_vertexai=False,
    )

    with pytest.raises(llm.LLMNotConfiguredError, match="only supports Gemini through Vertex AI"):
        llm.get_llm_client(settings)


def test_get_llm_client_vertex_requires_project(monkeypatch):
    settings = Settings(llm_mode="vertex", google_cloud_project="")
    monkeypatch.setattr(llm, "has_adc_credentials", lambda: True)
    monkeypatch.setattr(llm, "resolve_vertex_project_id", lambda explicit_project=None: None)

    with pytest.raises(llm.LLMNotConfiguredError, match="Google Cloud project"):
        llm.get_llm_client(settings)
