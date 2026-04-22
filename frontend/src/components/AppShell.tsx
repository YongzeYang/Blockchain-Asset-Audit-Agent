import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Sparkles,
  PlayCircle,
  History,
  Wand2,
  ShieldCheck,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useHealth } from '@/api/hooks';
import { InviteCodeButton } from './InviteCodeButton';

const NAV = [
  { to: '/', label: '总览', icon: LayoutDashboard, end: true },
  { to: '/skills', label: '技能库', icon: Sparkles },
  { to: '/audit/new', label: '新建审计', icon: PlayCircle },
  { to: '/runs', label: '运行历史', icon: History },
  { to: '/skills/new', label: '技能生成器', icon: Wand2 },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { data: health, isError } = useHealth();
  const ok = !!health && !isError && health.status === 'ok';
  return (
    <div className="flex min-h-full">
      <aside className="hidden w-60 shrink-0 border-r border-slate-200 bg-white md:flex md:flex-col">
        <div className="flex items-center gap-2 px-5 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white shadow-soft">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-900">区块链审计</p>
            <p className="text-[11px] text-slate-500">Audit Agent · MVP</p>
          </div>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition',
                  isActive
                    ? 'bg-brand-50 text-brand-700'
                    : 'text-slate-600 hover:bg-slate-100',
                )
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-slate-200 px-5 py-3 text-[11px] text-slate-400">
          v0.1.0 · 浅色 · 扁平
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between gap-3 border-b border-slate-200 bg-white/80 px-6 backdrop-blur">
          <div className="text-sm text-slate-500">
            <span className="text-slate-700">区块链资产审计 Agent 控制台</span>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <InviteCodeButton />
            <span
              className={cn(
                'badge',
                ok
                  ? 'bg-emerald-50 text-emerald-700 ring-emerald-200'
                  : 'bg-rose-50 text-rose-700 ring-rose-200',
              )}
            >
              <span
                className={cn(
                  'h-1.5 w-1.5 rounded-full',
                  ok ? 'bg-emerald-500' : 'bg-rose-500',
                )}
              />
              后端 {ok ? '在线' : '离线'}
            </span>
            {health?.llm_mode && (
              <span className="badge bg-slate-50 text-slate-600 ring-slate-200">
                LLM: {health.llm_mode}
              </span>
            )}
          </div>
        </header>
        <main className="flex-1 px-6 py-6">{children}</main>
      </div>
    </div>
  );
}
