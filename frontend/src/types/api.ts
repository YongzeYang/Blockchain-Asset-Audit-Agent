// Mirrors app/schemas/* on the backend.

export type Severity = 'info' | 'low' | 'medium' | 'high' | 'critical';
export type RunStatus = 'running' | 'completed' | 'failed' | string;
export type TxDirection = 'in' | 'out' | 'internal';

export interface ErrorResponse {
  error: string;
  detail?: string | null;
}

export interface HealthResponse {
  status: string;
  app: string;
  llm_mode: string;
}

export interface SkillDefinition {
  id: string;
  name: string;
  description: string;
  system_instruction: string;
  allowed_tools: string[];
  output_schema: string;
  tags: string[];
  risk_rules: string[];
  examples: string[];
  enabled: boolean;
  version: string;
}

export interface SkillDraftRequest {
  skill_name: string;
  domain?: string | null;
  expert_text: string;
  notes?: string | null;
}

export interface SkillDraftResponse {
  draft: SkillDefinition;
  yaml_preview: string;
}

export interface TimeRange {
  start?: string | null;
  end?: string | null;
}

export interface TransactionRecord {
  tx_hash: string;
  timestamp: string;
  chain: string;
  from_address: string;
  to_address: string;
  asset_symbol: string;
  amount: number;
  direction: TxDirection;
  tx_type: string;
  counterparty_label?: string | null;
  notes?: string | null;
}

export interface BalanceSnapshot {
  address: string;
  chain: string;
  asset_symbol: string;
  amount: number;
  usd_value?: number | null;
  timestamp?: string | null;
}

export interface LedgerEntry {
  entry_id?: string | null;
  timestamp?: string | null;
  asset_symbol: string;
  amount: number;
  direction: string;
  counterparty?: string | null;
  reference?: string | null;
}

export interface AuditRunRequest {
  skill_id?: string | null;
  objective: string;
  chain?: string | null;
  addresses: string[];
  time_range?: TimeRange | null;
  transactions: TransactionRecord[];
  balances: BalanceSnapshot[];
  ledger_entries: LedgerEntry[];
  address_labels: Record<string, string>;
  knowledge_texts: string[];
  extra_notes?: string | null;
  metadata: Record<string, string>;
}

export interface EvidenceRef {
  source_type: string;
  reference: string;
  detail?: string | null;
}

export interface AuditFinding {
  finding_id: string;
  title: string;
  severity: Severity;
  summary: string;
  rationale: string;
  evidence: EvidenceRef[];
  recommendation?: string | null;
}

export interface AuditAnomaly {
  anomaly_id: string;
  category: string;
  severity: Severity;
  description: string;
  related_tx_hashes: string[];
  evidence: EvidenceRef[];
}

export interface AuditReport {
  report_id: string;
  objective: string;
  scope_summary: string;
  executive_summary: string;
  net_flow_summary: string;
  findings: AuditFinding[];
  anomalies: AuditAnomaly[];
  open_questions: string[];
  recommended_next_steps: string[];
  confidence_note: string;
  limitations: string[];
}

export interface ToolCallLog {
  id: string;
  tool_name: string;
  args: Record<string, unknown>;
  result: unknown;
  created_at: string;
  error?: string | null;
}

export interface AuditRunResponse {
  run_id: string;
  status: string;
  skill_id: string;
  result: AuditReport;
  markdown_report: string;
  tool_calls: ToolCallLog[];
}

export interface RunSummary {
  run_id: string;
  skill_id: string;
  status: RunStatus;
  created_at: string;
  updated_at: string;
}

export interface RunDetailResponse {
  run_id: string;
  status: RunStatus;
  skill_id: string;
  input_payload: Record<string, unknown>;
  output_payload?: Record<string, unknown> | null;
  tool_calls: ToolCallLog[];
  error?: string | null;
  created_at: string;
  updated_at: string;
}
