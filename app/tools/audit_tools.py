"""Deterministic audit tools: net flows + rule-based checks."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from ..agent.run_context import RunContext
from ..config import get_settings
from ..schemas.audit import LedgerEntry, TransactionRecord
from ..utils.ids import new_id


def _load_address_book() -> dict[str, str]:
    p = Path(get_settings().address_book_path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k).lower().strip(): str(v) for k, v in data.items()}
    except Exception:
        return {}
    return {}


def _resolve_label(address: str, request_labels: dict[str, str], book: dict[str, str]) -> str | None:
    if not address:
        return None
    a = address.lower().strip()
    rl = {k.lower().strip(): v for k, v in (request_labels or {}).items()}
    return rl.get(a) or book.get(a)


def make_compute_net_flows(ctx: RunContext):
    def compute_net_flows() -> dict:
        """Compute inflow / outflow / net flow per (address, asset)."""
        req = ctx.request
        if req is None:
            return {"net_flows": [], "by_asset": {}}
        in_addrs = {a.lower().strip() for a in req.addresses}
        per_pair_in: dict[tuple[str, str], float] = defaultdict(float)
        per_pair_out: dict[tuple[str, str], float] = defaultdict(float)
        per_asset_in: dict[str, float] = defaultdict(float)
        per_asset_out: dict[str, float] = defaultdict(float)

        for tx in req.transactions:
            asset = tx.asset_symbol
            amt = float(tx.amount)
            direction = (tx.direction or "").lower()
            from_a = (tx.from_address or "").lower().strip()
            to_a = (tx.to_address or "").lower().strip()
            # Use the in-scope address for the (address, asset) pair when possible.
            if direction == "in":
                addr = to_a if not in_addrs or to_a in in_addrs else (next(iter(in_addrs), to_a))
                per_pair_in[(addr, asset)] += amt
                per_asset_in[asset] += amt
            elif direction == "out":
                addr = from_a if not in_addrs or from_a in in_addrs else (next(iter(in_addrs), from_a))
                per_pair_out[(addr, asset)] += amt
                per_asset_out[asset] += amt

        keys = set(per_pair_in.keys()) | set(per_pair_out.keys())
        net_flows = []
        for addr, asset in sorted(keys):
            inflow = per_pair_in.get((addr, asset), 0.0)
            outflow = per_pair_out.get((addr, asset), 0.0)
            net_flows.append(
                {
                    "address": addr,
                    "asset_symbol": asset,
                    "inflow": round(inflow, 8),
                    "outflow": round(outflow, 8),
                    "net": round(inflow - outflow, 8),
                }
            )
        by_asset = {
            a: {
                "inflow": round(per_asset_in.get(a, 0.0), 8),
                "outflow": round(per_asset_out.get(a, 0.0), 8),
                "net": round(per_asset_in.get(a, 0.0) - per_asset_out.get(a, 0.0), 8),
            }
            for a in sorted(set(per_asset_in) | set(per_asset_out))
        }
        return {"net_flows": net_flows, "by_asset": by_asset}

    return compute_net_flows


def _approx_equal(a: float, b: float, tol: float = 0.02) -> bool:
    if a == 0 and b == 0:
        return True
    base = max(abs(a), abs(b))
    if base == 0:
        return True
    return abs(a - b) / base <= tol


def _find_ledger_match(tx: TransactionRecord, ledger: list[LedgerEntry]) -> LedgerEntry | None:
    for entry in ledger:
        if entry.asset_symbol != tx.asset_symbol:
            continue
        if (entry.direction or "").lower() != (tx.direction or "").lower():
            continue
        if not _approx_equal(float(entry.amount), float(tx.amount)):
            continue
        if entry.timestamp and tx.timestamp:
            delta = abs((entry.timestamp - tx.timestamp).total_seconds())
            if delta > 86400 * 2:  # within 2 days
                continue
        return entry
    return None


def make_run_rule_based_checks(ctx: RunContext):
    def run_rule_based_checks() -> dict:
        """Run deterministic heuristics on the request and return anomalies.

        Heuristics:
        - unknown_counterparty: outgoing to address with no label
        - large_outgoing: amount >= LARGE_TX_THRESHOLD AND direction=out
        - first_seen_counterparty: first-time counterparty in this run
        - duplicate_same_day: same counterparty + asset hit multiple times same day
        - ledger_mismatch: no approximate ledger entry match
        - suspicious_approve: tx_type=approve to unknown spender
        """
        req = ctx.request
        if req is None:
            return {"summary": {}, "anomalies": [], "evidence": []}
        settings = get_settings()
        threshold = float(settings.large_tx_threshold)
        book = _load_address_book()

        anomalies: list[dict[str, Any]] = []
        evidence: list[dict[str, Any]] = []

        seen_counterparty: dict[str, str] = {}  # address -> first tx_hash seen
        per_day_counter: dict[tuple[str, str, str], list[str]] = defaultdict(list)

        for tx in req.transactions:
            counterparty = (tx.to_address if (tx.direction or "").lower() == "out" else tx.from_address) or ""
            cp_label = _resolve_label(counterparty, req.address_labels, book)
            day = tx.timestamp.date().isoformat() if isinstance(tx.timestamp, datetime) else str(tx.timestamp)[:10]

            # unknown_counterparty
            if (tx.direction or "").lower() == "out" and not cp_label:
                anomalies.append(
                    {
                        "anomaly_id": new_id("anom"),
                        "category": "unknown_counterparty",
                        "severity": "medium" if float(tx.amount) < threshold else "high",
                        "description": (
                            f"Outgoing {tx.amount} {tx.asset_symbol} to unlabeled counterparty {counterparty}."
                        ),
                        "related_tx_hashes": [tx.tx_hash],
                        "evidence": [
                            {"source_type": "transaction", "reference": tx.tx_hash, "detail": "unknown counterparty"}
                        ],
                    }
                )

            # large_outgoing
            if (tx.direction or "").lower() == "out" and float(tx.amount) >= threshold:
                anomalies.append(
                    {
                        "anomaly_id": new_id("anom"),
                        "category": "large_outgoing",
                        "severity": "high",
                        "description": (
                            f"Large outgoing transfer of {tx.amount} {tx.asset_symbol} "
                            f"(threshold {threshold}) to {counterparty}."
                        ),
                        "related_tx_hashes": [tx.tx_hash],
                        "evidence": [
                            {"source_type": "transaction", "reference": tx.tx_hash, "detail": "amount >= threshold"}
                        ],
                    }
                )

            # first_seen_counterparty
            cp_key = counterparty.lower().strip()
            if cp_key and cp_key not in seen_counterparty:
                seen_counterparty[cp_key] = tx.tx_hash

            # duplicate_same_day
            per_day_counter[(day, cp_key, tx.asset_symbol)].append(tx.tx_hash)

            # ledger_mismatch (only check outgoing with material amounts)
            if (tx.direction or "").lower() == "out":
                match = _find_ledger_match(tx, req.ledger_entries)
                if match is None and req.ledger_entries:
                    anomalies.append(
                        {
                            "anomaly_id": new_id("anom"),
                            "category": "ledger_mismatch",
                            "severity": "high" if float(tx.amount) >= threshold else "medium",
                            "description": (
                                f"No matching ledger entry found for outgoing {tx.amount} "
                                f"{tx.asset_symbol} ({tx.tx_hash})."
                            ),
                            "related_tx_hashes": [tx.tx_hash],
                            "evidence": [
                                {"source_type": "transaction", "reference": tx.tx_hash, "detail": "no ledger match"}
                            ],
                        }
                    )

            # suspicious_approve
            if (tx.tx_type or "").lower() == "approve" and not cp_label:
                anomalies.append(
                    {
                        "anomaly_id": new_id("anom"),
                        "category": "suspicious_approve",
                        "severity": "high",
                        "description": (
                            f"Approve call to unknown spender {counterparty} for asset {tx.asset_symbol}."
                        ),
                        "related_tx_hashes": [tx.tx_hash],
                        "evidence": [
                            {"source_type": "transaction", "reference": tx.tx_hash, "detail": "approve to unknown"}
                        ],
                    }
                )

            evidence.append(
                {"source_type": "transaction", "reference": tx.tx_hash, "detail": f"{tx.direction} {tx.amount} {tx.asset_symbol}"}
            )

        # First-seen counterparty (per run): emit anomalies for every unique cp
        for cp_key, tx_hash in seen_counterparty.items():
            anomalies.append(
                {
                    "anomaly_id": new_id("anom"),
                    "category": "first_seen_counterparty",
                    "severity": "low",
                    "description": f"Counterparty {cp_key} first seen in this audit window.",
                    "related_tx_hashes": [tx_hash],
                    "evidence": [{"source_type": "transaction", "reference": tx_hash, "detail": "first seen"}],
                }
            )

        # Duplicate same-day repeats
        for (day, cp_key, asset), tx_hashes in per_day_counter.items():
            if cp_key and len(tx_hashes) >= 2:
                anomalies.append(
                    {
                        "anomaly_id": new_id("anom"),
                        "category": "duplicate_same_day",
                        "severity": "medium",
                        "description": (
                            f"{len(tx_hashes)} transfers of {asset} to {cp_key} on {day} — possible split pattern."
                        ),
                        "related_tx_hashes": tx_hashes,
                        "evidence": [
                            {"source_type": "transaction", "reference": h, "detail": "same-day repeat"}
                            for h in tx_hashes
                        ],
                    }
                )

        summary = {
            "total_transactions": len(req.transactions),
            "total_anomalies": len(anomalies),
            "by_category": _count_by(anomalies, "category"),
            "by_severity": _count_by(anomalies, "severity"),
            "large_tx_threshold": threshold,
        }
        return {"summary": summary, "anomalies": anomalies, "evidence": evidence[:25]}

    return run_rule_based_checks


def _count_by(items: list[dict], key: str) -> dict[str, int]:
    out: dict[str, int] = defaultdict(int)
    for it in items:
        out[str(it.get(key, "unknown"))] += 1
    return dict(out)
