"""Load text/json/markdown files from knowledge directory and chunk them."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class KBChunk:
    source_id: str
    title: str
    text: str
    extra: dict = field(default_factory=dict)


def _chunk_markdown(text: str) -> list[tuple[str, str]]:
    """Split markdown by headings; falls back to blank-line paragraphs."""
    chunks: list[tuple[str, str]] = []
    current_title = "Intro"
    buffer: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if buffer:
                body = "\n".join(buffer).strip()
                if body:
                    chunks.append((current_title, body))
                buffer = []
            current_title = stripped.lstrip("# ").strip() or current_title
        else:
            buffer.append(line)
    if buffer:
        body = "\n".join(buffer).strip()
        if body:
            chunks.append((current_title, body))
    if not chunks:
        # Fallback to paragraph split.
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = [(f"Paragraph {i + 1}", p) for i, p in enumerate(paras)]
    return chunks


def load_chunks_from_dir(dir_path: str | Path) -> list[KBChunk]:
    p = Path(dir_path)
    chunks: list[KBChunk] = []
    if not p.exists():
        logger.warning("Knowledge directory %s does not exist", p)
        return chunks
    for f in sorted(p.rglob("*")):
        if not f.is_file():
            continue
        suffix = f.suffix.lower()
        try:
            if suffix in {".md", ".txt"}:
                content = f.read_text(encoding="utf-8")
                if suffix == ".md":
                    parts = _chunk_markdown(content)
                else:
                    parts = [
                        (f"{f.stem} #{i + 1}", chunk.strip())
                        for i, chunk in enumerate(content.split("\n\n"))
                        if chunk.strip()
                    ]
                for title, body in parts:
                    chunks.append(
                        KBChunk(
                            source_id=f"{f.stem}::{title[:60]}",
                            title=title,
                            text=body,
                            extra={"path": str(f)},
                        )
                    )
            elif suffix == ".json":
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for i, item in enumerate(data):
                        text = item.get("text") if isinstance(item, dict) else str(item)
                        title = item.get("title", f"{f.stem} #{i + 1}") if isinstance(item, dict) else f"{f.stem} #{i + 1}"
                        if text:
                            chunks.append(
                                KBChunk(
                                    source_id=f"{f.stem}::{i}",
                                    title=str(title),
                                    text=str(text),
                                    extra={"path": str(f)},
                                )
                            )
                elif isinstance(data, dict):
                    text = data.get("text") or json.dumps(data, ensure_ascii=False)
                    chunks.append(
                        KBChunk(
                            source_id=f.stem,
                            title=str(data.get("title", f.stem)),
                            text=text,
                            extra={"path": str(f)},
                        )
                    )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load knowledge file %s: %s", f, exc)
    logger.info("Loaded %d knowledge chunks from %s", len(chunks), p)
    return chunks
