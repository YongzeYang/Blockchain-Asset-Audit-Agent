import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Download,
  Copy,
  AlertCircle,
  ListChecks,
  HelpCircle,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import { useRunDetail } from '@/api/hooks';
import { Card, SectionTitle, Skeleton } from '@/components/Primitives';
import { SeverityBadge, StatusBadge } from '@/components/Badges';
import { JsonViewer } from '@/components/JsonViewer';
import { MarkdownView } from '@/components/MarkdownView';
import {
  cn,
  copyText,
  downloadText,
  formatDateTime,
  shortId,
} from '@/lib/utils';
import type {
  AuditAnomaly,
  AuditFinding,
  AuditReport,
  ToolCallLog,
} from '@/types/api';

type Tab = 'report' | 'markdown' | 'tools' | 'raw';

export default function RunDetailPage() {
  const { runId } = useParams();
  const { data, isLoading, isError } = useRunDetail(runId);
  const [tab, setTab] = useState<Tab>('report');

  const output = data?.output_payload as
    | {
        result?: AuditReport;
        markdown_report?: string;
        tool_calls?: ToolCallLog[];
        draft?: unknown;
        yaml_preview?: string;
      }
    | undefined;

  const report = output?.result;
  const markdown = output?.markdown_report;
  const tools = useMemo<ToolCallLog[]>(
    () => data?.tool_calls ?? output?.tool_calls ?? [],
    [data, output],
  );

  if (isLoading)
    return (
      <div className="space-y-3">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-72 w-full" />
      </div>
    );
  if (isError || !data)
    return (
      <Card>
        <p className="text-sm text-slate-500">未找到该运行记录。</p>
      </Card>
    );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link
            to="/runs"
            className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
          >
            <ArrowLeft className="h-4 w-4" /> 返回历史
          </Link>
          <span className="font-mono text-xs text-slate-400">
            {shortId(data.run_id, 12, 8)}
          </span>
          <button
            type="button"
            onClick={() => copyText(data.run_id, 'Run ID 已复制')}
            className="text-slate-400 hover:text-slate-600"
            title="复制 Run ID"
          >
            <Copy className="h-3.5 w-3.5" />
          </button>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <StatusBadge status={data.status} />
          <span>技能：{data.skill_id}</span>
          <span>· 创建 {formatDateTime(data.created_at)}</span>
        </div>
      </div>

      {data.error && (
        <Card className="border-rose-200 bg-rose-50/40">
          <div className="flex items-start gap-2 text-sm text-rose-700">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p className="font-medium">运行失败</p>
              <p className="mt-1 whitespace-pre-wrap text-xs">{data.error}</p>
            </div>
          </div>
        </Card>
      )}

      <div className="flex flex-wrap items-center gap-1 border-b border-slate-200">
        {(
          [
            { id: 'report', label: '报告' },
            { id: 'markdown', label: 'Markdown' },
            { id: 'tools', label: `工具调用 (${tools.length})` },
            { id: 'raw', label: '原始数据' },
          ] as { id: Tab; label: string }[]
        ).map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={cn(
              'border-b-2 px-3 py-2 text-sm font-medium transition',
              tab === t.id
                ? 'border-brand-600 text-brand-700'
                : 'border-transparent text-slate-500 hover:text-slate-700',
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'report' && (report ? <ReportView report={report} /> : <NoData what="结构化报告" />)}
      {tab === 'markdown' &&
        (markdown ? (
          <Card>
            <SectionTitle
              title="Markdown 报告"
              right={
                <div className="flex items-center gap-2">
                  <button
                    className="btn-ghost"
                    onClick={() => copyText(markdown)}
                  >
                    <Copy className="h-4 w-4" />
                    复制
                  </button>
                  <button
                    className="btn-secondary"
                    onClick={() =>
                      downloadText(`audit-${data.run_id}.md`, markdown, 'text/markdown')
                    }
                  >
                    <Download className="h-4 w-4" />
                    下载
                  </button>
                </div>
              }
            />
            <MarkdownView source={markdown} />
          </Card>
        ) : (
          <NoData what="Markdown 报告" />
        ))}
      {tab === 'tools' && <ToolTimeline tools={tools} />}
      {tab === 'raw' && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <SectionTitle title="输入 Payload" />
            <JsonViewer data={data.input_payload} />
          </Card>
          <Card>
            <SectionTitle title="输出 Payload" />
            <JsonViewer data={data.output_payload ?? null} />
          </Card>
        </div>
      )}
    </div>
  );
}

function NoData({ what }: { what: string }) {
  return (
    <Card>
      <p className="text-sm text-slate-500">该运行没有可用的{what}。</p>
    </Card>
  );
}

function ReportView({ report }: { report: AuditReport }) {
  return (
    <div className="space-y-4">
      <Card>
        <SectionTitle
          title="执行摘要"
          description={`目标：${report.objective}`}
        />
        <p className="whitespace-pre-wrap text-sm text-slate-800">
          {report.executive_summary}
        </p>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="rounded-lg bg-slate-50 p-3">
            <p className="text-xs font-medium text-slate-500">范围摘要</p>
            <p className="mt-1 text-sm text-slate-800">{report.scope_summary}</p>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <p className="text-xs font-medium text-slate-500">净流摘要</p>
            <p className="mt-1 text-sm text-slate-800">
              {report.net_flow_summary}
            </p>
          </div>
        </div>
      </Card>

      <Card>
        <SectionTitle
          title="发现"
          description={`${report.findings.length} 条`}
        />
        {report.findings.length === 0 ? (
          <p className="text-xs text-slate-400">无发现</p>
        ) : (
          <ul className="space-y-3">
            {report.findings.map((f) => (
              <FindingCard key={f.finding_id} f={f} />
            ))}
          </ul>
        )}
      </Card>

      <Card>
        <SectionTitle
          title="异常"
          description={`${report.anomalies.length} 条`}
        />
        {report.anomalies.length === 0 ? (
          <p className="text-xs text-slate-400">无异常</p>
        ) : (
          <ul className="space-y-3">
            {report.anomalies.map((a) => (
              <AnomalyCard key={a.anomaly_id} a={a} />
            ))}
          </ul>
        )}
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <SectionTitle title="待澄清问题" />
          <BulletList
            items={report.open_questions}
            empty="无"
            icon={<HelpCircle className="h-3.5 w-3.5 text-amber-500" />}
          />
        </Card>
        <Card>
          <SectionTitle title="建议下一步" />
          <BulletList
            items={report.recommended_next_steps}
            empty="无"
            icon={<ArrowRight className="h-3.5 w-3.5 text-brand-500" />}
          />
        </Card>
        <Card>
          <SectionTitle title="置信度说明" />
          <p className="text-sm text-slate-700">{report.confidence_note}</p>
        </Card>
        <Card>
          <SectionTitle title="局限性" />
          <BulletList
            items={report.limitations}
            empty="无"
            icon={<ShieldAlert className="h-3.5 w-3.5 text-slate-400" />}
          />
        </Card>
      </div>
    </div>
  );
}

function BulletList({
  items,
  empty,
  icon,
}: {
  items: string[];
  empty: string;
  icon?: React.ReactNode;
}) {
  if (!items || items.length === 0)
    return <p className="text-xs text-slate-400">{empty}</p>;
  return (
    <ul className="space-y-1.5 text-sm text-slate-700">
      {items.map((it, i) => (
        <li key={i} className="flex items-start gap-2">
          <span className="mt-1">{icon}</span>
          <span>{it}</span>
        </li>
      ))}
    </ul>
  );
}

function FindingCard({ f }: { f: AuditFinding }) {
  return (
    <li className="rounded-xl border border-slate-200 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-slate-900">{f.title}</p>
          <p className="font-mono text-[11px] text-slate-400">{f.finding_id}</p>
        </div>
        <SeverityBadge severity={f.severity} />
      </div>
      <p className="mt-2 text-sm text-slate-700">{f.summary}</p>
      <details className="mt-2 text-xs text-slate-600">
        <summary className="cursor-pointer text-slate-500 hover:text-slate-700">
          展开详情
        </summary>
        <div className="mt-2 space-y-2">
          <div>
            <p className="font-medium text-slate-500">推理</p>
            <p className="mt-0.5 whitespace-pre-wrap">{f.rationale}</p>
          </div>
          {f.recommendation && (
            <div>
              <p className="font-medium text-slate-500">建议</p>
              <p className="mt-0.5 whitespace-pre-wrap">{f.recommendation}</p>
            </div>
          )}
          {f.evidence.length > 0 && (
            <div>
              <p className="font-medium text-slate-500">证据</p>
              <ul className="mt-1 space-y-0.5">
                {f.evidence.map((e, i) => (
                  <li key={i} className="font-mono text-[11px]">
                    [{e.source_type}] {e.reference}
                    {e.detail ? ` — ${e.detail}` : ''}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </details>
    </li>
  );
}

function AnomalyCard({ a }: { a: AuditAnomaly }) {
  return (
    <li className="rounded-xl border border-slate-200 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-slate-900">{a.category}</p>
          <p className="font-mono text-[11px] text-slate-400">{a.anomaly_id}</p>
        </div>
        <SeverityBadge severity={a.severity} />
      </div>
      <p className="mt-2 text-sm text-slate-700">{a.description}</p>
      {a.related_tx_hashes.length > 0 && (
        <p className="mt-2 font-mono text-[11px] text-slate-500">
          相关交易：{a.related_tx_hashes.join(', ')}
        </p>
      )}
    </li>
  );
}

function ToolTimeline({ tools }: { tools: ToolCallLog[] }) {
  if (!tools || tools.length === 0) {
    return (
      <Card>
        <p className="text-sm text-slate-500">未触发任何工具调用。</p>
      </Card>
    );
  }
  return (
    <Card>
      <SectionTitle
        title="工具调用时间线"
        description="按发生顺序展示，每项可展开 args 与 result"
        right={<ListChecks className="h-4 w-4 text-slate-400" />}
      />
      <ol className="relative ml-3 space-y-4 border-l border-slate-200 pl-5">
        {tools.map((t) => (
          <li key={t.id} className="relative">
            <span className="absolute -left-[1.625rem] top-1 flex h-3 w-3 items-center justify-center rounded-full bg-brand-500 ring-4 ring-brand-100" />
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium text-slate-900">
                <span className="font-mono">{t.tool_name}</span>
                {t.error && (
                  <span className="ml-2 inline-flex rounded-full bg-rose-50 px-1.5 py-0.5 text-[10px] text-rose-700 ring-1 ring-rose-200">
                    错误
                  </span>
                )}
              </p>
              <span className="text-[11px] text-slate-400">
                {formatDateTime(t.created_at)}
              </span>
            </div>
            <details className="mt-2">
              <summary className="cursor-pointer text-xs text-slate-500 hover:text-slate-700">
                参数与结果
              </summary>
              <div className="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                <JsonViewer data={t.args} maxHeight="14rem" />
                <JsonViewer
                  data={t.error ? { error: t.error } : t.result}
                  maxHeight="14rem"
                />
              </div>
            </details>
          </li>
        ))}
      </ol>
    </Card>
  );
}
