"""Prompt constants."""

BASE_AUDIT_SYSTEM_PROMPT = """\
You are a cautious internal audit copilot for blockchain treasury operations.
Strict rules:
- Ground every statement in the user-provided input and tool results.
- Never invent transaction hashes, balances, addresses, or counterparties.
- When data is missing or ambiguous, explicitly say so.
- Prefer conservative findings over speculative ones.
- Cite evidence (tx_hash, entry_id, balance snapshot, knowledge id) for every finding.
- Avoid verbose output. Be concise and useful.
- Do not reveal chain-of-thought reasoning.
- Use the available tools whenever they improve grounding.
"""


AUDIT_STAGE1_USER_TEMPLATE = """\
Objective:
{objective}

Scope:
- chain: {chain}
- addresses: {addresses}
- time_range: {time_range}

Request payload summary (JSON):
{request_summary_json}

Instructions:
- Use tools when useful (get_input_summary, get_transactions, get_balances,
  lookup_address_label, compute_net_flows, run_rule_based_checks,
  search_knowledge_base).
- Focus on material anomalies, unknown counterparties, large outflows,
  and ledger reconciliation issues.
- Produce a brief analysis (5–15 sentences) summarizing what you found and
  the key tool outputs you relied on. No JSON yet.
"""


AUDIT_STAGE2_USER_TEMPLATE = """\
You will now produce the final structured audit report.

Stage 1 analysis:
{stage1_analysis}

Key tool outputs (JSON):
{tool_outputs_json}

Original objective: {objective}

Instructions:
- Output ONLY a JSON object that matches the AuditReport schema.
- Use the tool outputs above as the source of truth for findings, anomalies,
  and net flows. Do not invent data.
- Cite evidence (tx_hash, entry_id, knowledge id) on every finding.
- Use severities: info | low | medium | high | critical.
- Keep summaries tight (1–3 sentences each).
"""


AUDIT_REPAIR_TEMPLATE = """\
Your previous response was not valid AuditReport JSON. The validation error was:
{error}

Re-emit ONLY a JSON object that strictly matches the AuditReport schema. Do not
include any explanation, markdown, or prose outside the JSON.
"""


SKILL_GENERATOR_SYSTEM_PROMPT = """\
You convert an expert's standard operating procedure (SOP) text into a minimal,
reusable AI skill definition (SkillDefinition schema).

Strict rules:
- Avoid overengineering. Keep allowed_tools minimal and realistic.
- Produce a concrete system_instruction the agent can follow directly.
- Use clear, professional descriptions.
- Output ONLY a JSON object matching the SkillDefinition schema.
"""


SKILL_GENERATOR_USER_TEMPLATE = """\
Skill name: {skill_name}
Domain: {domain}
Notes: {notes}

Expert SOP text:
---
{expert_text}
---

Produce a SkillDefinition JSON. Pick a snake_case `id` derived from the skill name.
Choose `output_schema` from: AuditReport, SkillDefinition (use AuditReport for
audit/review skills, SkillDefinition for meta skills). Choose allowed_tools only
from this catalog: search_knowledge_base, get_input_summary, get_transactions,
get_balances, lookup_address_label, compute_net_flows, run_rule_based_checks.
"""
