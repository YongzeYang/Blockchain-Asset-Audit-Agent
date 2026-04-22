import type { AuditRunRequest } from '@/types/api';

export const EXAMPLE_AUDIT_REQUEST: AuditRunRequest = {
  skill_id: 'asset_audit_basic',
  objective:
    'Audit outgoing treasury transfers, identify unknown counterparties, and explain any material anomalies.',
  chain: 'ethereum',
  addresses: [
    '0x1111111111111111111111111111111111111111',
    '0x2222222222222222222222222222222222222222',
  ],
  time_range: {
    start: '2026-01-01T00:00:00+00:00',
    end: '2026-01-31T23:59:59+00:00',
  },
  transactions: [
    {
      tx_hash: '0xtx1',
      timestamp: '2026-01-05T10:12:00+00:00',
      chain: 'ethereum',
      from_address: '0x1111111111111111111111111111111111111111',
      to_address: '0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
      asset_symbol: 'USDC',
      amount: 25000,
      direction: 'out',
      tx_type: 'transfer',
    },
    {
      tx_hash: '0xtx2',
      timestamp: '2026-01-08T14:30:00+00:00',
      chain: 'ethereum',
      from_address: '0x1111111111111111111111111111111111111111',
      to_address: '0xdeaddeaddeaddeaddeaddeaddeaddeaddeaddead',
      asset_symbol: 'USDC',
      amount: 250000,
      direction: 'out',
      tx_type: 'transfer',
      notes: 'large outgoing to unknown counterparty',
    },
    {
      tx_hash: '0xtx3',
      timestamp: '2026-01-09T09:00:00+00:00',
      chain: 'ethereum',
      from_address: '0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
      to_address: '0x1111111111111111111111111111111111111111',
      asset_symbol: 'USDC',
      amount: 100000,
      direction: 'in',
      tx_type: 'transfer',
    },
    {
      tx_hash: '0xtx4',
      timestamp: '2026-01-15T16:45:00+00:00',
      chain: 'ethereum',
      from_address: '0x1111111111111111111111111111111111111111',
      to_address: '0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed',
      asset_symbol: 'USDC',
      amount: 5000,
      direction: 'out',
      tx_type: 'approve',
      notes: 'approve to unknown spender',
    },
  ],
  balances: [
    {
      address: '0x1111111111111111111111111111111111111111',
      chain: 'ethereum',
      asset_symbol: 'USDC',
      amount: 1500000,
      usd_value: 1500000,
      timestamp: '2026-01-31T23:59:00+00:00',
    },
  ],
  ledger_entries: [
    {
      entry_id: 'L-001',
      timestamp: '2026-01-05T10:00:00+00:00',
      asset_symbol: 'USDC',
      amount: 25000,
      direction: 'out',
      counterparty: 'Coinbase Deposit',
      reference: 'INV-2026-001',
    },
  ],
  address_labels: {
    '0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa': 'Coinbase Deposit',
  },
  knowledge_texts: [
    'Treasury policy: any single outgoing transfer >= 100,000 USD must be pre-approved by the CFO.',
  ],
  extra_notes: 'January monthly audit cycle.',
  metadata: { audit_period: '2026-01' },
};

export const EXAMPLE_EXPERT_SOP = `Treasury Outflow Audit — Internal SOP

When auditing treasury outflows the auditor proceeds as follows:

1. Reconcile every outgoing transfer to a ledger entry within 48 hours of the
   on-chain timestamp. Tolerate amount differences within 2 percent.
2. Flag any single outgoing transfer at or above 100,000 USD as material and
   require CFO sign-off.
3. Flag any outgoing transfer to a counterparty address that is not in the
   organization address book or in the request-time labels as unknown.
4. Flag any token approve call to a spender address that is not in the address
   book as suspicious.
5. Flag repeated transfers to the same counterparty on the same day as a
   possible split pattern.
6. Mark a finding High if it combines a material amount with an unknown
   counterparty or a missing ledger match. Mark Medium if either condition
   alone is met. Mark Low for first-seen counterparties without other risk.
7. Always cite the on-chain tx_hash or ledger entry_id in evidence.
8. Always list open questions for the treasury operator and recommended next
   steps before closing the audit.
`;
