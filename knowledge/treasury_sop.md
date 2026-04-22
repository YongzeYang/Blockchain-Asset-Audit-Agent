# Treasury Outflow Audit SOP

## Scope
This SOP applies to outgoing transfers from organization treasury wallets on
public blockchains (EVM, Bitcoin, etc.). It is intended for the internal audit
function performing read-only reviews of asset movements.

## Inputs
The auditor expects a normalized data set:
- Wallet addresses in scope
- Time range covered
- A list of normalized transactions (tx_hash, timestamp, from, to, asset, amount, direction)
- Most recent balance snapshots for each in-scope address
- The accounting ledger entries that should explain those movements
- Address labels (counterparty book) when available

## Procedure
1. Confirm completeness of the normalized transaction list against the chosen
   time range. Flag any time gaps.
2. Compute net inflows and outflows per address per asset.
3. Reconcile every material outflow to a ledger entry. A material outflow is
   any transfer at or above the configured large-tx threshold, or any transfer
   to a counterparty that is new to the organization.
4. Identify outgoing transfers to unknown counterparties (addresses without a
   label in the address book or request-time labels).
5. Identify suspicious approve calls — token approvals to spenders that are
   not in the address book.
6. Identify same-day repeated transfers to the same counterparty that may
   indicate splitting or test-then-drain patterns.
7. Document open questions for the treasury operator.

## Severity Guidance
- **Critical**: large outflow to unknown counterparty with no ledger match.
- **High**: large outflow to unknown counterparty OR ledger mismatch on a
  material outflow.
- **Medium**: unknown counterparty for a non-material amount, or first-seen
  counterparty pattern.
- **Low**: minor reconciliation gaps explainable by timing.
- **Info**: observational notes that are not findings.

## Output
The audit report must include an executive summary, a net flow summary, a
findings list with cited evidence (tx_hash or entry_id), an anomalies list,
open questions, recommended next steps, a confidence note, and a list of
limitations of the analysis.
