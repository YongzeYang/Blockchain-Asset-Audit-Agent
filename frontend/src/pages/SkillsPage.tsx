import { Link } from 'react-router-dom';
import { Wand2, Sparkles } from 'lucide-react';
import { useSkills } from '@/api/hooks';
import { Card, EmptyState, Skeleton } from '@/components/Primitives';
import { Tag } from '@/components/Badges';

export default function SkillsPage() {
  const { data, isLoading } = useSkills();
  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">技能库</h1>
          <p className="mt-1 text-sm text-slate-500">
            内置与自定义的审计技能，决定了 Agent 可使用的工具与系统提示。
          </p>
        </div>
        <Link to="/skills/new">
          <button className="btn-primary">
            <Wand2 className="h-4 w-4" />
            新增技能
          </button>
        </Link>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-44" />
          ))}
        </div>
      ) : !data || data.length === 0 ? (
        <EmptyState title="尚无技能" description="可通过技能生成器创建。" />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {data.map((s) => (
            <Link key={s.id} to={`/skills/${s.id}`}>
              <Card className="h-full transition hover:border-brand-200 hover:shadow">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                      <Sparkles className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-900">
                        {s.name}
                      </p>
                      <p className="font-mono text-[11px] text-slate-400">
                        {s.id} · v{s.version}
                      </p>
                    </div>
                  </div>
                  <span
                    className={
                      s.enabled
                        ? 'badge bg-emerald-50 text-emerald-700 ring-emerald-200'
                        : 'badge bg-slate-50 text-slate-500 ring-slate-200'
                    }
                  >
                    {s.enabled ? '启用' : '停用'}
                  </span>
                </div>
                <p className="mt-3 line-clamp-3 text-sm text-slate-600">
                  {s.description}
                </p>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {s.tags.slice(0, 5).map((t) => (
                    <Tag key={t}>{t}</Tag>
                  ))}
                </div>
                <div className="mt-3 text-xs text-slate-500">
                  允许工具 <span className="font-medium">{s.allowed_tools.length}</span> · 输出 <span className="font-mono">{s.output_schema}</span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
