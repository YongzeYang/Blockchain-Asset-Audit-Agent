"""Report rendering tool."""
from __future__ import annotations

from ..agent.run_context import RunContext
from ..utils.markdown import render_audit_report_markdown


def make_render_markdown_report(ctx: RunContext):
    def render_markdown_report(report: dict) -> dict:
        """Render the structured audit report dict as Markdown text.

        Args:
            report: An AuditReport-shaped dict.
        """
        md = render_audit_report_markdown(report or {})
        return {"markdown": md}

    return render_markdown_report
