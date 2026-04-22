import axios, { AxiosError } from 'axios';
import { toast } from 'sonner';
import type { ErrorResponse } from '@/types/api';
import { getInviteCode } from './inviteCode';

function resolveBaseUrl(): string {
  const explicitBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
  if (explicitBaseUrl) {
    return explicitBaseUrl;
  }

  if (import.meta.env.DEV) {
    return '/api';
  }

  if (typeof window !== 'undefined') {
    return `${window.location.protocol}//${window.location.hostname}:8042`;
  }

  return '/api';
}

const baseURL = resolveBaseUrl();

export const api = axios.create({
  baseURL,
  timeout: 120_000,
  headers: { 'Content-Type': 'application/json' },
});

// Attach the invite code header to every mutating request.
api.interceptors.request.use((config) => {
  const method = (config.method ?? 'get').toLowerCase();
  if (method !== 'get' && method !== 'head' && method !== 'options') {
    const code = getInviteCode();
    if (code) {
      config.headers = config.headers ?? {};
      (config.headers as Record<string, string>)['X-Invite-Code'] = code;
    }
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error: AxiosError<ErrorResponse>) => {
    const status = error.response?.status;
    const data = error.response?.data;
    let msg: string =
      (data && (data.detail || data.error)) ||
      error.message ||
      '请求失败';
    if (status === 401) {
      msg = '邀请码无效或缺失，请在右上角设置有效邀请码';
    }
    if (!error.config?.headers?.['x-silent']) {
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    return Promise.reject(error);
  },
);

export type ApiError = AxiosError<ErrorResponse>;
