"""Build per-run tool callables wired to a RunContext."""
from __future__ import annotations

import functools
import inspect
import logging
from typing import Callable

from ..kb.search import KnowledgeBase, get_kb
from ..schemas.skills import SkillDefinition
from ..tools.audit_tools import make_compute_net_flows, make_run_rule_based_checks
from ..tools.input_tools import (
    make_get_balances,
    make_get_input_summary,
    make_get_transactions,
    make_lookup_address_label,
)
from ..tools.kb_tools import make_search_knowledge_base
from ..tools.report_tools import make_render_markdown_report
from .run_context import RunContext

logger = logging.getLogger(__name__)


def _wrap_with_logging(name: str, fn: Callable, ctx: RunContext) -> Callable:
    sig = inspect.signature(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            args_dict = dict(bound.arguments)
        except TypeError:
            args_dict = {"args": list(args), "kwargs": kwargs}
        try:
            result = fn(*args, **kwargs)
            ctx.log_tool_call(name, args_dict, result=result)
            return result
        except Exception as exc:  # noqa: BLE001
            err = f"{type(exc).__name__}: {exc}"
            ctx.log_tool_call(name, args_dict, error=err)
            logger.exception("Tool %s raised an error", name)
            raise

    wrapper.__name__ = name
    wrapper.__doc__ = fn.__doc__
    wrapper.__annotations__ = dict(getattr(fn, "__annotations__", {}))
    try:
        wrapper.__signature__ = sig  # type: ignore[attr-defined]
    except Exception:
        pass
    return wrapper


def build_tools(
    skill: SkillDefinition,
    ctx: RunContext,
    kb: KnowledgeBase | None = None,
) -> dict[str, Callable]:
    """Build the dict of tool callables allowed for the given skill, bound to ctx."""
    kb = kb or get_kb()
    factories: dict[str, Callable] = {
        "search_knowledge_base": make_search_knowledge_base(ctx, kb),
        "get_input_summary": make_get_input_summary(ctx),
        "get_transactions": make_get_transactions(ctx),
        "get_balances": make_get_balances(ctx),
        "lookup_address_label": make_lookup_address_label(ctx),
        "compute_net_flows": make_compute_net_flows(ctx),
        "run_rule_based_checks": make_run_rule_based_checks(ctx),
        "render_markdown_report": make_render_markdown_report(ctx),
    }
    out: dict[str, Callable] = {}
    for name in skill.allowed_tools:
        if name not in factories:
            logger.warning("Skill %s requests unknown tool %s; skipping", skill.id, name)
            continue
        out[name] = _wrap_with_logging(name, factories[name], ctx)
    return out
