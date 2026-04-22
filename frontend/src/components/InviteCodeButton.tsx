import { useEffect, useRef, useState } from 'react';
import { Check, KeyRound, X } from 'lucide-react';
import { toast } from 'sonner';
import {
  getInviteCode,
  setInviteCode,
  subscribeInviteCode,
} from '@/lib/inviteCode';
import { cn } from '@/lib/utils';

export function InviteCodeButton() {
  const [code, setCode] = useState(() => getInviteCode());
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(code);
  const popRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => subscribeInviteCode(setCode), []);
  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (popRef.current && !popRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    window.addEventListener('mousedown', onClick);
    return () => window.removeEventListener('mousedown', onClick);
  }, [open]);

  const has = !!code;

  function save() {
    setInviteCode(draft.trim());
    toast.success(draft.trim() ? '邀请码已保存' : '邀请码已清除');
    setOpen(false);
  }

  return (
    <div className="relative" ref={popRef}>
      <button
        type="button"
        onClick={() => {
          setDraft(code);
          setOpen((v) => !v);
        }}
        className={cn(
          'badge cursor-pointer ring-1',
          has
            ? 'bg-emerald-50 text-emerald-700 ring-emerald-200 hover:bg-emerald-100'
            : 'bg-amber-50 text-amber-700 ring-amber-200 hover:bg-amber-100',
        )}
        title="设置邀请码 (X-Invite-Code)"
      >
        <KeyRound className="h-3 w-3" />
        邀请码 {has ? '已设' : '未设'}
      </button>
      {open && (
        <div className="absolute right-0 top-9 z-20 w-72 rounded-xl border border-slate-200 bg-white p-4 shadow-lg">
          <p className="text-sm font-medium text-slate-800">邀请码</p>
          <p className="mt-1 text-[11px] text-slate-500">
            所有写入请求会附带 <code className="rounded bg-slate-100 px-1">X-Invite-Code</code> 请求头。仅作部署期防滥用。
          </p>
          <input
            className="input mt-3"
            placeholder="输入邀请码"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && save()}
            autoFocus
          />
          <div className="mt-3 flex items-center justify-end gap-2">
            <button
              type="button"
              className="btn-ghost"
              onClick={() => {
                setDraft('');
                setInviteCode('');
                setOpen(false);
                toast.success('邀请码已清除');
              }}
            >
              <X className="h-3.5 w-3.5" /> 清除
            </button>
            <button type="button" className="btn-primary" onClick={save}>
              <Check className="h-3.5 w-3.5" /> 保存
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
