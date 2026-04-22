import { Link } from 'react-router-dom';
import { Activity, Sparkles, PlayCircle, History } from 'lucide-react';
import { useHealth, useRuns, useSkills } from '@/api/hooks';
import { Card, SectionTitle, Skeleton, EmptyState } from '@/components/Primitives';
import { StatusBadge } from '@/components/Badges';
import { formatDateTime, shortId } from '@/lib/utils';

export default function DashboardPage() {
  const { data: health, isLoading: hLoading } = useHealth();
  const { data: skills, isLoading: sLoading } = useSkills();
  const { data: runs, isLoading: rLoading } = useRuns(5);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">总览</h1>
        <p className="mt-1 text-sm text-slate-500">
          一站式查看后端状态、技能资产与最近的审计运行。
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
                后端状态
              </p>
              {hLoading ? (
                <Skeleton className="mt-2 h-7 w-24" />
              ) : (
                <p className="mt-2 text-2xl font-semibold text-slate-900">
                  {health?.status === 'ok' ? '在线' : '离线'}
                </p>
              )}
              <p className="mt-1 text-xs text-slate-500">
                LLM 模式 · {health?.llm_mode ?? '-'}
              </p>
            </div>
            <Activity className="h-8 w-8 text-brand-500" />
          </div>
        </Card>
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
                可用技能
              </p>
              {sLoading ? (
                <Skeleton className="mt-2 h-7 w-16" />
              ) : (
                <p className="mt-2 text-2xl font-semibold text-slate-900">
                  {skills?.length ?? 0}
                </p>
              )}
              <Link
                to="/skills"
                className="mt-1 inline-block text-xs text-brand-600 hover:underline"
              >
                查看全部 →
              </Link>
            </div>
            <Sparkles className="h-8 w-8 text-brand-500" />
          </div>
        </Card>
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
                快捷入口
              </p>
              <Link to="/audit/new" className="mt-2 inline-block">
                <button className="btn-primary">
                  <PlayCircle className="h-4 w-4" />
                  新建审计任务
                </button>
              </Link>
              <Link to="/skills/new" className="mt-2 ml-2 inline-block">
                <button className="btn-secondary">技能生成器</button>
              </Link>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <SectionTitle
          title="最近运行"
          description="最近 5 条审计与生成记录"
          right={
            <Link
              to="/runs"
              className="inline-flex items-center gap-1 text-xs text-brand-600 hover:underline"
            >
              <History className="h-3.5 w-3.5" /> 全部历史
            </Link>
          }
        />
        {rLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : !runs || runs.length === 0 ? (
          <EmptyState
            title="尚无运行记录"
            description="创建一次审计任务后，结果会持久化到本地数据库。"
            action={
              <Link to="/audit/new">
                <button className="btn-primary">开始第一个审计</button>
              </Link>
            }
          />
        ) : (
          <div className="overflow-hidden rounded-lg border border-slate-100">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-3 py-2 text-left">Run ID</th>
                  <th className="px-3 py-2 text-left">技能</th>
                  <th className="px-3 py-2 text-left">状态</th>
                  <th className="px-3 py-2 text-left">创建时间</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {runs.map((r) => (
                  <tr key={r.run_id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-mono text-xs">
                      <Link
                        to={`/runs/${r.run_id}`}
                        className="text-brand-600 hover:underline"
                      >
                        {shortId(r.run_id, 10, 6)}
                      </Link>
                    </td>
                    <td className="px-3 py-2 text-slate-700">{r.skill_id}</td>
                    <td className="px-3 py-2">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="px-3 py-2 text-slate-500">
                      {formatDateTime(r.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
