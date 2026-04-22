"""Pytest fixtures: force mock LLM mode and isolate the SQLite DB per session."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# Set env BEFORE importing app modules so settings cache picks them up.
_TMP = tempfile.mkdtemp(prefix="ai_agent_mvp_test_")
os.environ["LLM_MODE"] = "mock"
os.environ["APP_DB_PATH"] = str(Path(_TMP) / "agent.db")
# Make sure the project root is the cwd so skills/, knowledge/, data/ resolve.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

from fastapi.testclient import TestClient  # noqa: E402

from app.config import reset_settings_cache  # noqa: E402
from app.kb.search import reset_kb_for_tests  # noqa: E402
from app.skills.registry import reset_registry_for_tests  # noqa: E402

reset_settings_cache()
reset_registry_for_tests()
reset_kb_for_tests()

from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        # Tests bypass the public invite-code gate by sending a known-valid code.
        c.headers.update({"X-Invite-Code": "Chrissy"})
        yield c
