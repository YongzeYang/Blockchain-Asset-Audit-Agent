"""Gemini client backed by google-genai with Vertex AI."""
from __future__ import annotations

import json
import logging
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from .base import LLMClient, LLMProviderError, StructuredOutputError

logger = logging.getLogger(__name__)


class GeminiVertexClient(LLMClient):
    def __init__(
        self,
        project: str,
        location: str = "global",
        model: str = "gemini-2.5-flash",
        use_vertex: bool = True,
    ) -> None:
        try:
            from google import genai  # noqa: F401
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "google-genai is not installed; install it or use LLM_MODE=mock."
            ) from exc

        from google import genai

        self._genai = genai
        self._model = model
        self._project = project
        self._location = location
        self._client = genai.Client(
            vertexai=use_vertex,
            project=project,
            location=location,
        )

    def _normalize_error(self, exc: Exception) -> LLMProviderError:
        message = str(exc).strip() or type(exc).__name__
        return LLMProviderError(
            f"Vertex AI Gemini request failed for model '{self._model}' in location "
            f"'{self._location}': {message}"
        )

    # ------------------------------------------------------------------

    def generate_text(self, system: str, user: str) -> str:
        from google.genai import types

        try:
            resp = self._client.models.generate_content(
                model=self._model,
                contents=user,
                config=types.GenerateContentConfig(system_instruction=system),
            )
        except Exception as exc:  # noqa: BLE001
            raise self._normalize_error(exc) from exc
        return resp.text or ""

    def generate_with_tools(
        self,
        system: str,
        user: str,
        tools: dict[str, Callable],
    ) -> str:
        from google.genai import types

        callable_list = list(tools.values())
        config = types.GenerateContentConfig(
            system_instruction=system,
            tools=callable_list if callable_list else None,
        )
        try:
            resp = self._client.models.generate_content(
                model=self._model,
                contents=user,
                config=config,
            )
        except Exception as exc:  # noqa: BLE001
            raise self._normalize_error(exc) from exc
        return resp.text or ""

    def generate_structured(
        self,
        system: str,
        user: str,
        schema_model: type[BaseModel],
        extra_context: dict[str, Any] | None = None,
    ) -> BaseModel:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=schema_model,
        )
        try:
            resp = self._client.models.generate_content(
                model=self._model,
                contents=user,
                config=config,
            )
        except Exception as exc:  # noqa: BLE001
            raise self._normalize_error(exc) from exc
        # Prefer parsed if available.
        parsed = getattr(resp, "parsed", None)
        if isinstance(parsed, schema_model):
            return parsed
        text = resp.text or ""
        try:
            data = json.loads(text)
            return schema_model.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            # One repair pass.
            repair_user = (
                f"Your previous response was not valid {schema_model.__name__} JSON. "
                f"Error: {exc}. Re-emit ONLY a JSON object that strictly matches the schema."
            )
            try:
                resp2 = self._client.models.generate_content(
                    model=self._model,
                    contents=repair_user + "\n\nOriginal request:\n" + user,
                    config=config,
                )
            except Exception as exc2:  # noqa: BLE001
                raise self._normalize_error(exc2) from exc2
            parsed2 = getattr(resp2, "parsed", None)
            if isinstance(parsed2, schema_model):
                return parsed2
            try:
                data2 = json.loads(resp2.text or "")
                return schema_model.model_validate(data2)
            except (json.JSONDecodeError, ValidationError) as exc2:
                raise StructuredOutputError(
                    f"Failed to obtain valid {schema_model.__name__} JSON: {exc2}"
                ) from exc2
