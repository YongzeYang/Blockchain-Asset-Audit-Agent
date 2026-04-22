import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, PlayCircle } from 'lucide-react';
import { useSkill } from '@/api/hooks';
import { Card, SectionTitle, Skeleton } from '@/components/Primitives';
import { Tag } from '@/components/Badges';

export default function SkillDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data, isLoading } = useSkill(id);

  if (isLoading) {
    return <Skeleton className="h-96 w-full" />;
  }
  if (!data) {
    return (
      <Card>
        <p className="text-sm text-slate-500">未找到该技能。</p>
      </Card>
    );
  }
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link
          to="/skills"
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
        >
          <ArrowLeft className="h-4 w-4" /> 返回技能库
        </Link>
        <button
          className="btn-primary"
          onClick={() => navigate(`/audit/new?skill=${data.id}`)}
        >
          <PlayCircle className="h-4 w-4" />
          用此技能审计
        </button>
      </div>

      <Card>
        <SectionTitle
          title={data.name}
          description={`${data.id} · v${data.version} · 输出 ${data.output_schema}`}
          right={
            <span
              className={
                data.enabled
                  ? 'badge bg-emerald-50 text-emerald-700 ring-emerald-200'
                  : 'badge bg-slate-50 text-slate-500 ring-slate-200'
              }
            >
              {data.enabled ? '启用' : '停用'}
            </span>
          }
        />
        <p className="text-sm text-slate-700">{data.description}</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {data.tags.map((t) => (
            <Tag key={t}>{t}</Tag>
          ))}
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <SectionTitle title="系统提示" />
          <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-3 font-mono text-xs text-slate-800">
            {data.system_instruction}
          </pre>
        </Card>
        <Card>
          <SectionTitle title="允许工具" />
          <ul className="space-y-1 text-sm">
            {data.allowed_tools.map((t) => (
              <li key={t} className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-brand-400" />
                <span className="font-mono text-slate-700">{t}</span>
              </li>
            ))}
          </ul>
        </Card>
        <Card>
          <SectionTitle title="风险规则" />
          {data.risk_rules.length === 0 ? (
            <p className="text-xs text-slate-400">未配置</p>
          ) : (
            <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
              {data.risk_rules.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          )}
        </Card>
        <Card>
          <SectionTitle title="示例" />
          {data.examples.length === 0 ? (
            <p className="text-xs text-slate-400">未配置</p>
          ) : (
            <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
              {data.examples.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
