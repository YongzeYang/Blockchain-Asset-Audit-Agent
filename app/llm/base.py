"""LLM client base interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable

from pydantic import BaseModel


class LLMClient(ABC):
    @abstractmethod
    def generate_text(self, system: str, user: str) -> str: ...

    @abstractmethod
    def generate_with_tools(
        self,
        system: str,
        user: str,
        tools: dict[str, Callable],
    ) -> str:
        """Run the model with tool calling. Returns final text response."""

    @abstractmethod
    def generate_structured(
        self,
        system: str,
        user: str,
        schema_model: type[BaseModel],
        extra_context: dict[str, Any] | None = None,
    ) -> BaseModel:
        """Generate a JSON object validated against schema_model."""


class StructuredOutputError(Exception):
    pass


class LLMProviderError(Exception):
    pass
