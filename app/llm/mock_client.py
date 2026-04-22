"""Deterministic mock LLM client used by tests and local mock mode.

This client does NOT call any external service. It uses the provided python
tool callables to produce realistic, grounded outputs so the rest of the
system (including tool logging and persistence) is exercised end-to-end.
"""
from __future__ import annotations

import re
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from ..schemas.audit import AuditReport
from ..schemas.skills import SkillDefinition
from ..utils.ids import new_id
from .base import LLMClient, StructuredOutputError


def _slugify(value: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", value or "").strip("_").lower()
    return s or "skill"


def _extract_bullets(text: str) -> list[str]:
    bullets: list[str] = []
    for line in (text or "").splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith(("-", "*", "•")) or re.match(r"^\d+[.)]\s", s):
            cleaned = re.sub(r"^[-*•\d.)\s]+", "", s).strip()
            if cleaned:
                bullets.append(cleaned)
    return bullets[:12]


class MockLLMClient(LLMClient):
    """Mock client that exercises tools and produces grounded structured outputs."""

    def generate_text(self, system: str, user: str) -> str:
        return "[mock] OK"

    def generate_with_tools(
        self,
        system: str,
        user: str,
        tools: dict[str, Callable],
    ) -> str:
        """Invoke a fixed set of tools to gather context, then summarize."""
        notes: list[str] = ["[mock] Stage-1 grounded analysis."]

        def call(name: str, **kwargs):
            fn = tools.get(name)
            if fn is None:
                return None
            try:
                return fn(**kwargs)
            except Exception as exc:  # noqa: BLE001
                notes.append(f"- tool {name} failed: {exc}")
                return None

        summary = call("get_input_summary")
        if summary:
            notes.append(
                f"- Scope: {summary.get('address_count', 0)} addresses, "
                f"{summary.get('transaction_count', 0)} transactions, "
                f"{summary.get('ledger_count', 0)} ledger entries."
            )
        flows = call("compute_net_flows")
        if flows and flows.get("by_asset"):
            top = ", ".join(
                f"{a}: net {v['net']}" for a, v in list(flows["by_asset"].items())[:5]
            )
            notes.append(f"- Net flow by asset: {top}.")
        checks = call("run_rule_based_checks")
        if checks:
            sev = checks.get("summary", {}).get("by_severity", {})
            notes.append(
                f"- Rule checks found {checks.get('summary', {}).get('total_anomalies', 0)} anomalies "
                f"({sev})."
            )
        # Touch the KB to produce a tool log.
        call("search_knowledge_base", query="treasury outflow audit", top_k=3)
        return "\n".join(notes)

    def generate_structured(
        self,
        system: str,
        user: str,
        schema_model: type[BaseModel],
        extra_context: dict[str, Any] | None = None,
    ) -> BaseModel:
        ctx = extra_context or {}
        if schema_model is AuditReport:
            return self._mock_audit_report(ctx)
        if schema_model is SkillDefinition:
            return self._mock_skill_definition(ctx)
        raise StructuredOutputError(
            f"MockLLMClient does not know how to generate {schema_model.__name__}"
        )

    # ------------------------------------------------------------------
    # AuditReport mock
    # ------------------------------------------------------------------

    def _mock_audit_report(self, ctx: dict[str, Any]) -> AuditReport:
        request = ctx.get("request")
        rule_checks = ctx.get("rule_checks") or {}
        net_flows = ctx.get("net_flows") or {}
        stage1 = ctx.get("stage1_analysis") or ""

        objective = getattr(request, "objective", "Audit objective")
        addresses = list(getattr(request, "addresses", []) or [])
        chain = getattr(request, "chain", None) or "unknown"

        anomalies_in = rule_checks.get("anomalies", []) or []
        # Promote the highest-severity anomalies to findings.
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        sorted_anoms = sorted(
            anomalies_in,
            key=lambda a: severity_order.get(str(a.get("severity", "info")).lower(), 0),
            reverse=True,
        )
        findings = []
        for a in sorted_anoms[:5]:
            findings.append(
                {
                    "finding_id": new_id("find"),
                    "title": f"{a.get('category', 'finding').replace('_', ' ').title()}",
                    "severity": a.get("severity", "medium"),
                    "summary": a.get("description", ""),
                    "rationale": (
                        "Derived from deterministic rule-based checks on the provided "
                        "transactions, balances, and ledger entries."
                    ),
                    "evidence": a.get("evidence", []),
                    "recommendation": "Investigate counterparty and reconcile with operations.",
                }
            )

        by_asset = net_flows.get("by_asset", {}) if isinstance(net_flows, dict) else {}
        if by_asset:
            nf_summary = "; ".join(
                f"{a}: in={v.get('inflow', 0)}, out={v.get('outflow', 0)}, net={v.get('net', 0)}"
                for a, v in by_asset.items()
            )
        else:
            nf_summary = "No transaction data available to compute net flows."

        report = AuditReport(
            report_id=new_id("rpt"),
            objective=objective,
            scope_summary=(
                f"{len(addresses)} address(es) on chain {chain}; "
                f"{len(getattr(request, 'transactions', []) or [])} transactions, "
                f"{len(getattr(request, 'balances', []) or [])} balance snapshots, "
                f"{len(getattr(request, 'ledger_entries', []) or [])} ledger entries."
            ),
            executive_summary=(
                f"[mock] Reviewed scope. "
                f"{rule_checks.get('summary', {}).get('total_anomalies', 0)} anomalies detected by "
                f"deterministic checks. See findings for the highest-severity items."
            ),
            net_flow_summary=nf_summary,
            findings=findings,
            anomalies=[
                {
                    "anomaly_id": a.get("anomaly_id", new_id("anom")),
                    "category": a.get("category", "unknown"),
                    "severity": a.get("severity", "info"),
                    "description": a.get("description", ""),
                    "related_tx_hashes": a.get("related_tx_hashes", []),
                    "evidence": a.get("evidence", []),
                }
                for a in anomalies_in
            ],
            open_questions=[
                "Are any of the unlabeled counterparties known to operations?",
                "Is the ledger snapshot complete for the requested time range?",
            ],
            recommended_next_steps=[
                "Reach out to operations to label unknown counterparties.",
                "Reconcile any flagged outgoing transfers with bookkeeping records.",
                "Re-run the audit after labels and ledger entries are updated.",
            ],
            confidence_note=(
                "Findings are produced by deterministic heuristics in mock mode; "
                "treat severities as indicative."
            ),
            limitations=[
                "Mock LLM mode — no Gemini reasoning was applied.",
                "Only the data provided in the request was analyzed; no on-chain lookups were performed.",
            ],
        )
        return report

    # ------------------------------------------------------------------
    # SkillDefinition mock
    # ------------------------------------------------------------------

    def _mock_skill_definition(self, ctx: dict[str, Any]) -> SkillDefinition:
        req = ctx.get("draft_request")
        skill_name = getattr(req, "skill_name", None) or "Generated Skill"
        domain = getattr(req, "domain", None) or "general"
        expert_text = getattr(req, "expert_text", "") or ""
        notes = getattr(req, "notes", None)

        bullets = _extract_bullets(expert_text)
        risk_rules = bullets[:6] if bullets else []
        # Heuristic: if the SOP mentions transactions/treasury/audit, lean on audit tools.
        text_l = expert_text.lower()
        is_audit_like = any(
            kw in text_l
            for kw in ("audit", "treasury", "transaction", "ledger", "outflow", "counterparty")
        )
        if is_audit_like:
            allowed_tools = [
                "search_knowledge_base",
                "get_input_summary",
                "get_transactions",
                "compute_net_flows",
                "run_rule_based_checks",
            ]
            output_schema = "AuditReport"
        else:
            allowed_tools = ["search_knowledge_base"]
            output_schema = "SkillDefinition"

        sys_instr_parts = [
            f"You are an expert agent for: {skill_name}.",
            f"Domain: {domain}.",
            "Ground every statement in user-provided input and tool results.",
            "Be concise, cite evidence, and never invent data.",
        ]
        if bullets:
            sys_instr_parts.append("Follow these procedural rules:")
            sys_instr_parts.extend(f"- {b}" for b in bullets[:8])
        if notes:
            sys_instr_parts.append(f"Operator notes: {notes}")

        skill_id = _slugify(skill_name)
        return SkillDefinition(
            id=skill_id,
            name=skill_name,
            description=(
                f"[mock] Auto-generated skill draft for {skill_name} "
                f"based on {len(bullets)} extracted procedure bullet(s)."
            ),
            system_instruction="\n".join(sys_instr_parts),
            allowed_tools=allowed_tools,
            output_schema=output_schema,
            tags=[domain, "draft"],
            risk_rules=risk_rules,
            examples=[],
            enabled=True,
            version="0.1.0",
        )
