"""Knowledge base tool implementations."""
from __future__ import annotations

from dataclasses import asdict

from ..agent.run_context import RunContext
from ..kb.search import KnowledgeBase


def make_search_knowledge_base(ctx: RunContext, kb: KnowledgeBase):
    def search_knowledge_base(query: str, top_k: int = 5) -> dict:
        """Search the local knowledge documents and per-request snippets.

        Args:
            query: A natural-language query string.
            top_k: Maximum number of results to return.
        """
        extras = list(ctx.request.knowledge_texts) if ctx.request else []
        results = kb.search(query, top_k=top_k, extra_texts=extras)
        return {
            "query": query,
            "results": [
                {
                    "source_id": r.source_id,
                    "title": r.title,
                    "snippet": r.snippet,
                    "score": r.score,
                }
                for r in results
            ],
        }

    return search_knowledge_base
