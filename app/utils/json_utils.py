"""JSON serialization utilities that handle datetimes and pydantic models."""
from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


def _default(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f"Type {type(obj)!r} is not JSON serializable")


def dumps(value: Any) -> str:
    return json.dumps(value, default=_default, ensure_ascii=False)


def loads(value: str | bytes | None) -> Any:
    if value is None or value == "":
        return None
    return json.loads(value)
