import { Link } from 'react-router-dom';
import { useRuns } from '@/api/hooks';
import { Card, EmptyState, Skeleton } from '@/components/Primitives';
import { StatusBadge } from '@/components/Badges';
import { formatDateTime, shortId } from '@/lib/utils';

export default function RunsPage() {
  const { data, isLoading } = useRuns(50);
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">运行历史</h1>
        <p className="mt-1 text-sm text-slate-500">
          每次审计或技能生成都会作为一条 Run 记录持久化，可点击进入回放。
        </p>
      </div>
      <Card className="p-0">
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-10" />
            ))}
          </div>
        ) : !data || data.length === 0 ? (
          <div className="p-6">
            <EmptyState
              title="尚无运行记录"
              description="新建一个审计任务后，结果会出现在这里。"
              action={
                <Link to="/audit/new">
                  <button className="btn-primary">新建审计</button>
                </Link>
              }
            />
          </div>
        ) : (
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3 text-left">Run ID</th>
                <th className="px-4 py-3 text-left">技能</th>
                <th className="px-4 py-3 text-left">状态</th>
                <th className="px-4 py-3 text-left">创建</th>
                <th className="px-4 py-3 text-left">更新</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((r) => (
                <tr key={r.run_id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-mono text-xs">
                    <Link
                      to={`/runs/${r.run_id}`}
                      className="text-brand-600 hover:underline"
                    >
                      {shortId(r.run_id, 12, 6)}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-700">{r.skill_id}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={r.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {formatDateTime(r.created_at)}
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {formatDateTime(r.updated_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
