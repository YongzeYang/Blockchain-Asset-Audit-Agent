import { useState } from 'react';
import { ChevronRight, Copy } from 'lucide-react';
import { cn, copyText } from '@/lib/utils';

interface JsonViewerProps {
  data: unknown;
  collapsed?: boolean;
  className?: string;
  maxHeight?: string;
}

export function JsonViewer({
  data,
  collapsed = false,
  className,
  maxHeight = '24rem',
}: JsonViewerProps) {
  const [open, setOpen] = useState(!collapsed);
  const text = JSON.stringify(data, null, 2);
  return (
    <div className={cn('rounded-lg bg-slate-900 text-slate-100', className)}>
      <div className="flex items-center justify-between border-b border-white/10 px-3 py-1.5 text-xs">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="inline-flex items-center gap-1 text-slate-300 hover:text-white"
        >
          <ChevronRight
            className={cn('h-3.5 w-3.5 transition', open && 'rotate-90')}
          />
          JSON
        </button>
        <button
          type="button"
          onClick={() => copyText(text)}
          className="inline-flex items-center gap-1 text-slate-300 hover:text-white"
        >
          <Copy className="h-3.5 w-3.5" />
          复制
        </button>
      </div>
      {open && (
        <pre
          className="overflow-auto px-3 py-2 font-mono text-xs leading-relaxed"
          style={{ maxHeight }}
        >
          <code>{text}</code>
        </pre>
      )}
    </div>
  );
}
