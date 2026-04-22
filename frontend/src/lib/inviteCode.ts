// Lightweight client-side store for the invite code (X-Invite-Code header).
// Persisted to localStorage; consumed by axios request interceptor in src/lib/api.ts.

const KEY = 'invite_code';
type Listener = (code: string) => void;
const listeners = new Set<Listener>();

export function getInviteCode(): string {
  try {
    return localStorage.getItem(KEY) ?? '';
  } catch {
    return '';
  }
}

export function setInviteCode(code: string): void {
  try {
    if (code) localStorage.setItem(KEY, code);
    else localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
  listeners.forEach((fn) => fn(code));
}

export function subscribeInviteCode(fn: Listener): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}
