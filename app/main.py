"""FastAPI application entrypoint."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import agent as agent_api
from .api import audit as audit_api
from .api import health as health_api
from .api import runs as runs_api
from .api import skills as skills_api
from .config import get_settings
from .kb.search import get_kb
from .llm import LLMNotConfiguredError
from .llm.base import LLMProviderError, StructuredOutputError
from .logging_config import configure_logging
from .schemas.common import ErrorResponse
from .skills.registry import UnknownSkillError, get_registry
from .storage.db import init_db

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Backend-only AI Agent MVP for blockchain asset audit (Gemini via Vertex AI).",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _on_startup() -> None:
        init_db()
        get_registry()  # load skills
        get_kb()  # load knowledge
        logger.info(
            "App started: name=%s env=%s llm_mode=%s model=%s",
            settings.app_name,
            settings.app_env,
            settings.llm_mode,
            settings.gemini_model,
        )

    @app.exception_handler(UnknownSkillError)
    async def _unknown_skill(_: Request, exc: UnknownSkillError):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(error="unknown_skill", detail=str(exc)).model_dump(),
        )

    @app.exception_handler(LLMNotConfiguredError)
    async def _llm_not_configured(_: Request, exc: LLMNotConfiguredError):
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(error="llm_not_configured", detail=str(exc)).model_dump(),
        )

    @app.exception_handler(StructuredOutputError)
    async def _structured_error(_: Request, exc: StructuredOutputError):
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(error="structured_output_failed", detail=str(exc)).model_dump(),
        )

    @app.exception_handler(LLMProviderError)
    async def _llm_provider_error(_: Request, exc: LLMProviderError):
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(error="llm_provider_error", detail=str(exc)).model_dump(),
        )

    @app.exception_handler(Exception)
    async def _generic(_: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error="internal_error", detail="Internal server error").model_dump(),
        )

    app.include_router(health_api.router)
    app.include_router(skills_api.router)
    app.include_router(audit_api.router)
    app.include_router(agent_api.router)
    app.include_router(runs_api.router)
    return app


app = create_app()
