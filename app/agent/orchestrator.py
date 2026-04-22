"""Agent orchestrator: audit run + skill draft generation."""
from __future__ import annotations

import logging
from typing import Any

from ..config import get_settings
from ..llm import LLMNotConfiguredError, get_llm_client
from ..llm.base import StructuredOutputError
from ..llm.prompts import (
    AUDIT_STAGE1_USER_TEMPLATE,
    AUDIT_STAGE2_USER_TEMPLATE,
    BASE_AUDIT_SYSTEM_PROMPT,
    SKILL_GENERATOR_SYSTEM_PROMPT,
    SKILL_GENERATOR_USER_TEMPLATE,
)
from ..schemas.audit import AuditReport, AuditRunRequest, AuditRunResponse
from ..schemas.skills import SkillDefinition, SkillDraftRequest, SkillDraftResponse
from ..skills.loader import skill_to_yaml
from ..skills.registry import UnknownSkillError, get_registry
from ..storage import run_repository
from ..tools.report_tools import make_render_markdown_report
from ..utils.ids import new_id
from ..utils.json_utils import dumps
from .run_context import RunContext
from .tool_factory import build_tools

logger = logging.getLogger(__name__)


def _request_summary_for_prompt(req: AuditRunRequest) -> dict:
    return {
        "objective": req.objective,
        "chain": req.chain,
        "addresses": req.addresses,
        "transaction_count": len(req.transactions),
        "balance_count": len(req.balances),
        "ledger_count": len(req.ledger_entries),
        "address_label_count": len(req.address_labels),
        "knowledge_text_count": len(req.knowledge_texts),
        "extra_notes": req.extra_notes,
    }


def run_audit(request: AuditRunRequest) -> AuditRunResponse:
    settings = get_settings()
    registry = get_registry()
    skill_id = request.skill_id or settings.default_skill_id
    skill = registry.get(skill_id)  # raises UnknownSkillError

    run_id = new_id("run")
    run_repository.create_run(
        run_id=run_id,
        skill_id=skill.id,
        status="running",
        input_payload=request.model_dump(mode="json"),
    )

    ctx = RunContext(run_id=run_id, request=request)
    tools = build_tools(skill, ctx)
    llm = get_llm_client(settings)

    try:
        # Stage 1: tool-using analysis.
        stage1_user = AUDIT_STAGE1_USER_TEMPLATE.format(
            objective=request.objective,
            chain=request.chain or "unknown",
            addresses=", ".join(request.addresses) if request.addresses else "(none)",
            time_range=(
                request.time_range.model_dump_json() if request.time_range else "(none)"
            ),
            request_summary_json=dumps(_request_summary_for_prompt(request)),
        )
        stage1_system = BASE_AUDIT_SYSTEM_PROMPT + "\n\n" + (skill.system_instruction or "")
        stage1_analysis = llm.generate_with_tools(
            system=stage1_system,
            user=stage1_user,
            tools=tools,
        )

        # Safety net: ensure deterministic outputs even if the model didn't call them.
        rule_checks = _ensure_tool_called(ctx, tools, "run_rule_based_checks")
        net_flows = _ensure_tool_called(ctx, tools, "compute_net_flows")

        # Stage 2: structured report.
        tool_outputs = {
            "compute_net_flows": net_flows,
            "run_rule_based_checks": rule_checks,
        }
        stage2_user = AUDIT_STAGE2_USER_TEMPLATE.format(
            stage1_analysis=stage1_analysis or "(empty)",
            tool_outputs_json=dumps(tool_outputs),
            objective=request.objective,
        )
        try:
            report = llm.generate_structured(
                system=BASE_AUDIT_SYSTEM_PROMPT,
                user=stage2_user,
                schema_model=AuditReport,
                extra_context={
                    "request": request,
                    "rule_checks": rule_checks,
                    "net_flows": net_flows,
                    "stage1_analysis": stage1_analysis,
                },
            )
        except StructuredOutputError:
            run_repository.update_run(
                run_id, status="failed", error_text="Structured output validation failed."
            )
            raise

        # Render markdown via the tool wrapper so it gets logged.
        render = make_render_markdown_report(ctx)
        rendered = render(report.model_dump(mode="json"))
        markdown_report = rendered.get("markdown", "")
        # Manual log (render not bound through factory).
        ctx.log_tool_call(
            "render_markdown_report",
            {"report": "<truncated>"},
            result={"markdown_length": len(markdown_report)},
        )

        response = AuditRunResponse(
            run_id=run_id,
            status="completed",
            skill_id=skill.id,
            result=report,
            markdown_report=markdown_report,
            tool_calls=list(ctx.tool_calls),
        )

        # Persist tool calls + final output.
        for call in ctx.tool_calls:
            try:
                run_repository.add_tool_call(call, run_id=run_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to persist tool call %s: %s", call.id, exc)
        run_repository.update_run(
            run_id,
            status="completed",
            output_payload=response.model_dump(mode="json"),
        )
        return response

    except UnknownSkillError:
        run_repository.update_run(run_id, status="failed", error_text="Unknown skill.")
        raise
    except LLMNotConfiguredError as exc:
        run_repository.update_run(run_id, status="failed", error_text=str(exc))
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Audit run failed")
        run_repository.update_run(run_id, status="failed", error_text=str(exc))
        # Still persist any tool calls captured before failure.
        for call in ctx.tool_calls:
            try:
                run_repository.add_tool_call(call, run_id=run_id)
            except Exception:
                pass
        raise


def _ensure_tool_called(ctx: RunContext, tools: dict[str, Any], name: str) -> dict | None:
    """If `name` was called during stage 1, return its latest result; else call it now."""
    for call in reversed(ctx.tool_calls):
        if call.tool_name == name and call.error is None:
            return call.result if isinstance(call.result, dict) else {"value": call.result}
    fn = tools.get(name)
    if fn is None:
        return None
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Safety-net call to %s failed: %s", name, exc)
        return None


def run_skill_draft(request: SkillDraftRequest) -> SkillDraftResponse:
    settings = get_settings()
    registry = get_registry()
    # Use the meta skill if present (for system instruction); otherwise fall back to defaults.
    try:
        skill = registry.get("skill_generator_basic")
        system_prompt = SKILL_GENERATOR_SYSTEM_PROMPT + "\n\n" + (skill.system_instruction or "")
    except UnknownSkillError:
        system_prompt = SKILL_GENERATOR_SYSTEM_PROMPT

    run_id = new_id("run")
    run_repository.create_run(
        run_id=run_id,
        skill_id="skill_generator_basic",
        status="running",
        input_payload=request.model_dump(mode="json"),
    )

    llm = get_llm_client(settings)
    try:
        user_prompt = SKILL_GENERATOR_USER_TEMPLATE.format(
            skill_name=request.skill_name,
            domain=request.domain or "(unspecified)",
            notes=request.notes or "(none)",
            expert_text=request.expert_text or "",
        )
        draft = llm.generate_structured(
            system=system_prompt,
            user=user_prompt,
            schema_model=SkillDefinition,
            extra_context={"draft_request": request},
        )
        yaml_preview = skill_to_yaml(draft)
        response = SkillDraftResponse(draft=draft, yaml_preview=yaml_preview)
        run_repository.update_run(
            run_id,
            status="completed",
            output_payload=response.model_dump(mode="json"),
        )
        return response
    except Exception as exc:  # noqa: BLE001
        logger.exception("Skill draft generation failed")
        run_repository.update_run(run_id, status="failed", error_text=str(exc))
        raise
