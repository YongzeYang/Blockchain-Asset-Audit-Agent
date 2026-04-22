"""Tools that expose normalized request input to the agent."""
from __future__ import annotations

import json
from pathlib import Path

from ..agent.run_context import RunContext
from ..config import get_settings


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


def make_get_input_summary(ctx: RunContext):
    def get_input_summary() -> dict:
        """Return high-level counts and summaries of the request input."""
        req = ctx.request
        if req is None:
            return {"error": "no request bound"}
        chains = sorted({t.chain for t in req.transactions})
        assets = sorted({t.asset_symbol for t in req.transactions} | {b.asset_symbol for b in req.balances})
        return {
            "objective": req.objective,
            "chain": req.chain,
            "address_count": len(req.addresses),
            "addresses": req.addresses,
            "transaction_count": len(req.transactions),
            "balance_count": len(req.balances),
            "ledger_count": len(req.ledger_entries),
            "knowledge_text_count": len(req.knowledge_texts),
            "address_label_count": len(req.address_labels),
            "chains_seen": chains,
            "assets_seen": assets,
            "time_range": req.time_range.model_dump(mode="json") if req.time_range else None,
            "extra_notes": req.extra_notes,
        }

    return get_input_summary


def make_get_transactions(ctx: RunContext):
    def get_transactions(limit: int = 200) -> dict:
        """Return normalized transactions, capped to a safe size.

        Args:
            limit: Maximum number of transactions to return (defaults to 200).
        """
        req = ctx.request
        if req is None:
            return {"transactions": [], "total": 0, "returned": 0}
        items = [t.model_dump(mode="json") for t in req.transactions[: max(0, int(limit))]]
        return {
            "transactions": items,
            "total": len(req.transactions),
            "returned": len(items),
        }

    return get_transactions


def make_get_balances(ctx: RunContext):
    def get_balances() -> dict:
        """Return balance snapshots from the request."""
        req = ctx.request
        if req is None:
            return {"balances": [], "total": 0}
        items = [b.model_dump(mode="json") for b in req.balances]
        return {"balances": items, "total": len(items)}

    return get_balances


def make_lookup_address_label(ctx: RunContext):
    def lookup_address_label(address: str) -> dict:
        """Look up a label for the given address.

        Searches request-time address_labels first, then falls back to the
        local data/address_book.json file.

        Args:
            address: The address to look up (case-insensitive).
        """
        req = ctx.request
        addr = (address or "").lower().strip()
        if not addr:
            return {"address": address, "label": None, "source": None}
        if req:
            req_labels = {k.lower().strip(): v for k, v in req.address_labels.items()}
            if addr in req_labels:
                return {"address": addr, "label": req_labels[addr], "source": "request"}
        book = _load_address_book()
        if addr in book:
            return {"address": addr, "label": book[addr], "source": "address_book"}
        return {"address": addr, "label": None, "source": None}

    return lookup_address_label
