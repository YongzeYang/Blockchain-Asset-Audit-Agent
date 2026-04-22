"""Markdown rendering helpers for audit reports."""
from __future__ import annotations

from typing import Any, Iterable


def _esc(text: Any) -> str:
    if text is None:
        return ""
    return str(text).replace("\n", " ").strip()


def bullet_list(items: Iterable[Any]) -> str:
    items = [i for i in items if i not in (None, "")]
    if not items:
        return "_None._"
    return "\n".join(f"- {_esc(i)}" for i in items)


def render_audit_report_markdown(report: dict) -> str:
    """Render an AuditReport dict as Markdown text."""
    lines: list[str] = []
    lines.append(f"# Audit Report — {_esc(report.get('report_id', ''))}")
    lines.append("")
    if obj := report.get("objective"):
        lines.append(f"**Objective:** {_esc(obj)}")
        lines.append("")
    if scope := report.get("scope_summary"):
        lines.append("## Scope")
        lines.append(_esc(scope))
        lines.append("")
    if exec_sum := report.get("executive_summary"):
        lines.append("## Executive Summary")
        lines.append(_esc(exec_sum))
        lines.append("")
    if nf := report.get("net_flow_summary"):
        lines.append("## Net Flow Summary")
        lines.append(_esc(nf))
        lines.append("")

    findings = report.get("findings") or []
    lines.append("## Findings")
    if not findings:
        lines.append("_No findings._")
    else:
        for f in findings:
            lines.append(f"### [{_esc(f.get('severity','info')).upper()}] {_esc(f.get('title',''))}")
            lines.append(f"- **ID:** {_esc(f.get('finding_id',''))}")
            lines.append(f"- **Summary:** {_esc(f.get('summary',''))}")
            if f.get("rationale"):
                lines.append(f"- **Rationale:** {_esc(f.get('rationale'))}")
            if f.get("recommendation"):
                lines.append(f"- **Recommendation:** {_esc(f.get('recommendation'))}")
            ev = f.get("evidence") or []
            if ev:
                lines.append("- **Evidence:**")
                for e in ev:
                    lines.append(
                        f"  - `{_esc(e.get('source_type',''))}` "
                        f"{_esc(e.get('reference',''))} — {_esc(e.get('detail',''))}"
                    )
            lines.append("")

    anomalies = report.get("anomalies") or []
    lines.append("## Anomalies")
    if not anomalies:
        lines.append("_No anomalies._")
    else:
        for a in anomalies:
            lines.append(
                f"- **[{_esc(a.get('severity','info')).upper()}] "
                f"{_esc(a.get('category',''))}** — {_esc(a.get('description',''))}"
            )
            tx = a.get("related_tx_hashes") or []
            if tx:
                lines.append(f"  - related tx: {', '.join(_esc(t) for t in tx)}")
        lines.append("")

    if oq := report.get("open_questions"):
        lines.append("## Open Questions")
        lines.append(bullet_list(oq))
        lines.append("")
    if ns := report.get("recommended_next_steps"):
        lines.append("## Recommended Next Steps")
        lines.append(bullet_list(ns))
        lines.append("")
    if cn := report.get("confidence_note"):
        lines.append("## Confidence")
        lines.append(_esc(cn))
        lines.append("")
    if lim := report.get("limitations"):
        lines.append("## Limitations")
        lines.append(bullet_list(lim))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
