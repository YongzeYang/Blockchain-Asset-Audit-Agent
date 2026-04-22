"""Per-run execution context that captures tool call logs."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..schemas.audit import AuditRunRequest
from ..schemas.common import ToolCallLog
from ..utils.ids import new_id
from ..utils.time_utils import utcnow


@dataclass
class RunContext:
    run_id: str
    request: AuditRunRequest | None = None
    tool_calls: list[ToolCallLog] = field(default_factory=list)
    created_at: datetime = field(default_factory=utcnow)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def log_tool_call(
        self,
        tool_name: str,
        args: dict[str, Any],
        result: Any | None = None,
        error: str | None = None,
    ) -> ToolCallLog:
        entry = ToolCallLog(
            id=new_id("tc"),
            tool_name=tool_name,
            args=args or {},
            result=result,
            error=error,
            created_at=utcnow(),
        )
        with self._lock:
            self.tool_calls.append(entry)
        return entry
