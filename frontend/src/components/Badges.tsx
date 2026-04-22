import { cn } from '@/lib/utils';
import type { Severity, RunStatus } from '@/types/api';

const SEVERITY_STYLE: Record<Severity, string> = {
  info: 'bg-slate-50 text-slate-700 ring-slate-200',
  low: 'bg-sky-50 text-sky-700 ring-sky-200',
  medium: 'bg-amber-50 text-amber-700 ring-amber-200',
  high: 'bg-orange-50 text-orange-700 ring-orange-200',
  critical: 'bg-rose-50 text-rose-700 ring-rose-200',
};

const SEVERITY_LABEL: Record<Severity, string> = {
  info: '信息',
  low: '低',
  medium: '中',
  high: '高',
  critical: '严重',
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  const cls = SEVERITY_STYLE[severity] ?? SEVERITY_STYLE.info;
  return <span className={cn('badge', cls)}>{SEVERITY_LABEL[severity] ?? severity}</span>;
}

export function StatusBadge({ status }: { status: RunStatus }) {
  const map: Record<string, string> = {
    completed: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
    running: 'bg-sky-50 text-sky-700 ring-sky-200',
    failed: 'bg-rose-50 text-rose-700 ring-rose-200',
  };
  const labels: Record<string, string> = {
    completed: '已完成',
    running: '执行中',
    failed: '失败',
  };
  const cls = map[status] ?? 'bg-slate-50 text-slate-700 ring-slate-200';
  return <span className={cn('badge', cls)}>{labels[status] ?? status}</span>;
}

export function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="badge bg-brand-50 text-brand-700 ring-brand-100">{children}</span>
  );
}
