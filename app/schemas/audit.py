"""Audit input/output schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .common import EvidenceRef, TimeRange, ToolCallLog


class TransactionRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    tx_hash: str
    timestamp: datetime
    chain: str
    from_address: str
    to_address: str
    asset_symbol: str
    amount: float
    direction: str  # "in" | "out" | "internal"
    tx_type: str  # transfer | approve | swap | contract_call ...
    counterparty_label: str | None = None
    notes: str | None = None


class BalanceSnapshot(BaseModel):
    model_config = ConfigDict(extra="ignore")
    address: str
    chain: str
    asset_symbol: str
    amount: float
    usd_value: float | None = None
    timestamp: datetime | None = None


class LedgerEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    entry_id: str | None = None
    timestamp: datetime | None = None
    asset_symbol: str
    amount: float
    direction: str
    counterparty: str | None = None
    reference: str | None = None


class AuditRunRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    skill_id: str | None = None
    objective: str
    chain: str | None = None
    addresses: list[str] = Field(default_factory=list)
    time_range: TimeRange | None = None
    transactions: list[TransactionRecord] = Field(default_factory=list)
    balances: list[BalanceSnapshot] = Field(default_factory=list)
    ledger_entries: list[LedgerEntry] = Field(default_factory=list)
    address_labels: dict[str, str] = Field(default_factory=dict)
    knowledge_texts: list[str] = Field(default_factory=list)
    extra_notes: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class AuditFinding(BaseModel):
    model_config = ConfigDict(extra="ignore")
    finding_id: str
    title: str
    severity: str  # info | low | medium | high | critical
    summary: str
    rationale: str
    evidence: list[EvidenceRef] = Field(default_factory=list)
    recommendation: str | None = None


class AuditAnomaly(BaseModel):
    model_config = ConfigDict(extra="ignore")
    anomaly_id: str
    category: str
    severity: str
    description: str
    related_tx_hashes: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)


class AuditReport(BaseModel):
    model_config = ConfigDict(extra="ignore")
    report_id: str
    objective: str
    scope_summary: str
    executive_summary: str
    net_flow_summary: str
    findings: list[AuditFinding] = Field(default_factory=list)
    anomalies: list[AuditAnomaly] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    confidence_note: str
    limitations: list[str] = Field(default_factory=list)


class AuditRunResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    run_id: str
    status: str
    skill_id: str
    result: AuditReport
    markdown_report: str
    tool_calls: list[ToolCallLog] = Field(default_factory=list)
