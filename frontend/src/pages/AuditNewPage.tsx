import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { FileJson, Loader2, PlayCircle, RefreshCw } from 'lucide-react';
import { useRunAudit, useSkills } from '@/api/hooks';
import { Card, EmptyState, Field, SectionTitle } from '@/components/Primitives';
import { JsonViewer } from '@/components/JsonViewer';
import { EXAMPLE_AUDIT_REQUEST } from '@/data/examples';
import type { AuditRunRequest } from '@/types/api';

const EMPTY_PAYLOAD: AuditRunRequest = {
  skill_id: '',
  objective: '',
  chain: '',
  addresses: [],
  time_range: { start: '', end: '' },
  transactions: [],
  balances: [],
  ledger_entries: [],
  address_labels: {},
  knowledge_texts: [],
  extra_notes: '',
  metadata: {},
};

export default function AuditNewPage() {
  const [params] = useSearchParams();
  const presetSkill = params.get('skill') ?? undefined;
  const navigate = useNavigate();
  const { data: skills } = useSkills();
  const audit = useRunAudit();

  const [payload, setPayload] = useState<AuditRunRequest>({
    ...EMPTY_PAYLOAD,
    skill_id: presetSkill ?? '',
  });
  const [jsonText, setJsonText] = useState<string>(() =>
    JSON.stringify(payload, null, 2),
  );
  const [jsonError, setJsonError] = useState<string | null>(null);

  // Sync structured -> json text when not actively editing JSON
  useEffect(() => {
    setJsonText(JSON.stringify(payload, null, 2));
  }, [payload]);

  const auditSkills = useMemo(
    () => (skills ?? []).filter((s) => s.output_schema === 'AuditReport'),
    [skills],
  );

  const updateField = <K extends keyof AuditRunRequest>(
    key: K,
    value: AuditRunRequest[K],
  ) => setPayload((p) => ({ ...p, [key]: value }));

  function loadExample() {
    setPayload({ ...EXAMPLE_AUDIT_REQUEST });
    toast.success('已载入示例 Payload');
  }

  function applyJson() {
    try {
      const parsed = JSON.parse(jsonText) as AuditRunRequest;
      if (typeof parsed !== 'object' || !parsed)
        throw new Error('必须是一个 JSON 对象');
      setPayload(parsed);
      setJsonError(null);
      toast.success('已应用 JSON 修改');
    } catch (e) {
      setJsonError(e instanceof Error ? e.message : String(e));
    }
  }

  async function submit() {
    if (!payload.objective?.trim()) {
      toast.error('请填写审计目标 (objective)');
      return;
    }
    try {
      const res = await audit.mutateAsync(payload);
      toast.success('审计完成');
      navigate(`/runs/${res.run_id}`);
    } catch {
      // toast 由 axios 拦截器处理
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">新建审计</h1>
          <p className="mt-1 text-sm text-slate-500">
            配置参数并提交至 <span className="font-mono">/v1/audit/run</span>。后端为同步执行，可能需要数秒到数十秒。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" className="btn-secondary" onClick={loadExample}>
            <RefreshCw className="h-4 w-4" /> 载入示例
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={submit}
            disabled={audit.isPending}
          >
            {audit.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <PlayCircle className="h-4 w-4" />
            )}
            {audit.isPending ? '执行中…' : '运行审计'}
          </button>
        </div>
      </div>

      {audit.isPending && (
        <Card className="border-brand-200 bg-brand-50/30">
          <div className="flex items-center gap-3 text-sm text-brand-800">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在执行 Agent 流水线（工具调用 + 结构化报告生成），请耐心等待…
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <SectionTitle title="基本信息" />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Field label="技能 (skill_id)">
              <select
                className="input"
                value={payload.skill_id ?? ''}
                onChange={(e) => updateField('skill_id', e.target.value || null)}
              >
                <option value="">使用默认技能</option>
                {auditSkills.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.id})
                  </option>
                ))}
              </select>
            </Field>
            <Field label="区块链 (chain)">
              <input
                className="input"
                value={payload.chain ?? ''}
                onChange={(e) => updateField('chain', e.target.value)}
                placeholder="ethereum"
              />
            </Field>
            <Field label="审计目标 (objective)" hint="必填">
              <textarea
                className="input"
                rows={3}
                value={payload.objective}
                onChange={(e) => updateField('objective', e.target.value)}
              />
            </Field>
            <Field label="附加备注 (extra_notes)">
              <textarea
                className="input"
                rows={3}
                value={payload.extra_notes ?? ''}
                onChange={(e) => updateField('extra_notes', e.target.value)}
              />
            </Field>
            <Field label="时间范围 起" hint="ISO 8601, 可留空">
              <input
                className="input"
                value={payload.time_range?.start ?? ''}
                onChange={(e) =>
                  updateField('time_range', {
                    ...(payload.time_range ?? {}),
                    start: e.target.value,
                  })
                }
                placeholder="2026-01-01T00:00:00+00:00"
              />
            </Field>
            <Field label="时间范围 止">
              <input
                className="input"
                value={payload.time_range?.end ?? ''}
                onChange={(e) =>
                  updateField('time_range', {
                    ...(payload.time_range ?? {}),
                    end: e.target.value,
                  })
                }
                placeholder="2026-01-31T23:59:59+00:00"
              />
            </Field>
            <Field label="审计地址 (addresses, 逗号分隔)">
              <textarea
                className="input"
                rows={3}
                value={payload.addresses.join(',\n')}
                onChange={(e) =>
                  updateField(
                    'addresses',
                    e.target.value
                      .split(/[\s,]+/)
                      .map((s) => s.trim())
                      .filter(Boolean),
                  )
                }
                placeholder="0x..."
              />
            </Field>
            <Field label="知识文本 (knowledge_texts, 每行一条)">
              <textarea
                className="input"
                rows={3}
                value={payload.knowledge_texts.join('\n')}
                onChange={(e) =>
                  updateField(
                    'knowledge_texts',
                    e.target.value.split('\n').filter((s) => s.trim()),
                  )
                }
              />
            </Field>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
            <DataCount label="交易记录" count={payload.transactions.length} />
            <DataCount label="余额快照" count={payload.balances.length} />
            <DataCount label="账本分录" count={payload.ledger_entries.length} />
          </div>
          <p className="mt-3 text-xs text-slate-500">
            交易/余额/账本的明细数据请在右侧 JSON 编辑器中以数组形式提供。点击「载入示例」可一键填充。
          </p>
        </Card>

        <Card>
          <SectionTitle
            title="完整 Payload (JSON)"
            description="结构化字段会同步到这里；编辑 JSON 后点击「应用 JSON」覆盖结构化字段。"
            right={
              <button
                type="button"
                className="btn-ghost"
                onClick={applyJson}
                title="解析并应用"
              >
                <FileJson className="h-4 w-4" />
                应用 JSON
              </button>
            }
          />
          <textarea
            className="input min-h-[28rem] font-mono text-xs"
            value={jsonText}
            onChange={(e) => {
              setJsonText(e.target.value);
              setJsonError(null);
            }}
            spellCheck={false}
          />
          {jsonError && (
            <p className="mt-2 text-xs text-rose-600">JSON 解析失败：{jsonError}</p>
          )}
        </Card>
      </div>

      {audit.data && (
        <Card>
          <SectionTitle title="最近一次响应" />
          <JsonViewer data={audit.data} collapsed maxHeight="20rem" />
        </Card>
      )}

      {(skills?.length ?? 0) === 0 && (
        <EmptyState
          title="未发现任何技能"
          description="请确认后端已启动且 skills/ 目录非空。"
        />
      )}
    </div>
  );
}

function DataCount({ label, count }: { label: string; count: number }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-900">{count}</p>
    </div>
  );
}
