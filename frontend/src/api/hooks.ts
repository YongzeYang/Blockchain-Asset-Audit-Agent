import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type {
  AuditRunRequest,
  AuditRunResponse,
  HealthResponse,
  RunDetailResponse,
  RunSummary,
  SkillDefinition,
  SkillDraftRequest,
  SkillDraftResponse,
} from '@/types/api';

// Health
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => (await api.get<HealthResponse>('/health')).data,
    refetchInterval: 30_000,
  });
}

// Skills
export function useSkills() {
  return useQuery({
    queryKey: ['skills'],
    queryFn: async () => (await api.get<SkillDefinition[]>('/v1/skills')).data,
  });
}

export function useSkill(id?: string) {
  return useQuery({
    queryKey: ['skill', id],
    enabled: !!id,
    queryFn: async () =>
      (await api.get<SkillDefinition>(`/v1/skills/${id}`)).data,
  });
}

export function useGenerateSkill() {
  return useMutation({
    mutationFn: async (body: SkillDraftRequest) =>
      (await api.post<SkillDraftResponse>('/v1/skills/generate', body)).data,
  });
}

export function useSaveSkill() {
  return useMutation({
    mutationFn: async (body: SkillDefinition) =>
      (await api.post('/v1/skills/save', body)).data,
  });
}

// Audit
export function useRunAudit() {
  return useMutation({
    mutationFn: async (body: AuditRunRequest) =>
      (await api.post<AuditRunResponse>('/v1/audit/run', body)).data,
  });
}

// Runs
export function useRuns(limit = 50) {
  return useQuery({
    queryKey: ['runs', limit],
    queryFn: async () =>
      (await api.get<RunSummary[]>('/v1/runs', { params: { limit } })).data,
  });
}

export function useRunDetail(runId?: string) {
  return useQuery({
    queryKey: ['run', runId],
    enabled: !!runId,
    queryFn: async () =>
      (await api.get<RunDetailResponse>(`/v1/runs/${runId}`)).data,
  });
}
