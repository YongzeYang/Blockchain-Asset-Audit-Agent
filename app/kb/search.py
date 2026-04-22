"""Lightweight lexical search across KB chunks plus per-request snippets."""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import Iterable

from ..config import get_settings
from .loader import KBChunk, load_chunks_from_dir

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text or "")}


@dataclass
class SearchResult:
    source_id: str
    title: str
    snippet: str
    score: float


def _score(query: str, q_tokens: set[str], chunk_text: str) -> float:
    if not q_tokens:
        return 0.0
    c_tokens = _tokens(chunk_text)
    if not c_tokens:
        return 0.0
    overlap = len(q_tokens & c_tokens)
    if overlap == 0:
        return 0.0
    base = overlap / max(1, len(q_tokens))
    phrase_bonus = 0.25 if query.strip().lower() in chunk_text.lower() else 0.0
    return round(base + phrase_bonus, 4)


def _snippet(text: str, max_len: int = 280) -> str:
    text = text.strip().replace("\n\n", " \n")
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


class KnowledgeBase:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._chunks: list[KBChunk] = []

    def load(self) -> None:
        settings = get_settings()
        with self._lock:
            self._chunks = load_chunks_from_dir(settings.knowledge_dir)

    def chunks(self) -> list[KBChunk]:
        with self._lock:
            return list(self._chunks)

    def search(
        self,
        query: str,
        top_k: int = 5,
        extra_texts: Iterable[str] | None = None,
    ) -> list[SearchResult]:
        q_tokens = _tokens(query)
        results: list[SearchResult] = []
        for ch in self.chunks():
            s = _score(query, q_tokens, ch.text + " " + ch.title)
            if s > 0:
                results.append(
                    SearchResult(
                        source_id=ch.source_id,
                        title=ch.title,
                        snippet=_snippet(ch.text),
                        score=s,
                    )
                )
        if extra_texts:
            for i, t in enumerate(extra_texts):
                if not t:
                    continue
                s = _score(query, q_tokens, t)
                if s > 0:
                    results.append(
                        SearchResult(
                            source_id=f"request::{i}",
                            title=f"Request snippet #{i + 1}",
                            snippet=_snippet(t),
                            score=s,
                        )
                    )
        results.sort(key=lambda r: r.score, reverse=True)
        return results[: max(0, top_k)]


_kb: KnowledgeBase | None = None
_kb_lock = threading.Lock()


def get_kb() -> KnowledgeBase:
    global _kb
    if _kb is None:
        with _kb_lock:
            if _kb is None:
                _kb = KnowledgeBase()
                _kb.load()
    return _kb


def reset_kb_for_tests() -> None:
    global _kb
    _kb = None
