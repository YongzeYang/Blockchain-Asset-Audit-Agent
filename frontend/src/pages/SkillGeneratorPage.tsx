import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Loader2, RefreshCw, Save, Wand2 } from 'lucide-react';
import { useGenerateSkill, useSaveSkill } from '@/api/hooks';
import { Card, Field, SectionTitle } from '@/components/Primitives';
import { Tag } from '@/components/Badges';
import { EXAMPLE_EXPERT_SOP } from '@/data/examples';
import type { SkillDefinition, SkillDraftResponse } from '@/types/api';

export default function SkillGeneratorPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    skill_name: '',
    domain: 'blockchain-audit',
    expert_text: '',
    notes: '',
  });
  const [draft, setDraft] = useState<SkillDraftResponse | null>(null);
  const [editedDraft, setEditedDraft] = useState<SkillDefinition | null>(null);

  const generate = useGenerateSkill();
  const save = useSaveSkill();

  function loadExample() {
    setForm((f) => ({
      ...f,
      skill_name: f.skill_name || 'AML Multi Sig Review',
      expert_text: EXAMPLE_EXPERT_SOP,
    }));
    toast.success('已载入示例 SOP 文本');
  }

  async function onGenerate() {
    if (!form.skill_name.trim() || !form.expert_text.trim()) {
      toast.error('请填写技能名称与专家文本');
      return;
    }
    const res = await generate.mutateAsync({
      skill_name: form.skill_name,
      domain: form.domain || undefined,
      expert_text: form.expert_text,
      notes: form.notes || undefined,
    });
    setDraft(res);
    setEditedDraft(res.draft);
  }

  async function onSave() {
    if (!editedDraft) return;
    await save.mutateAsync(editedDraft);
    toast.success(`技能 ${editedDraft.id} 已保存`);
    navigate(`/skills/${editedDraft.id}`);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">技能生成器</h1>
        <p className="mt-1 text-sm text-slate-500">
          将专家 SOP 文本转换为结构化 Skill 草稿，确认无误后保存到技能库。
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <SectionTitle
            title="专家输入"
            right={
              <button className="btn-ghost" type="button" onClick={loadExample}>
                <RefreshCw className="h-4 w-4" />
                载入示例
              </button>
            }
          />
          <div className="space-y-4">
            <Field label="技能名称">
              <input
                className="input"
                value={form.skill_name}
                onChange={(e) =>
                  setForm({ ...form, skill_name: e.target.value })
                }
                placeholder="AML Multi Sig Review"
              />
            </Field>
            <Field label="领域 (domain)">
              <input
                className="input"
                value={form.domain}
                onChange={(e) => setForm({ ...form, domain: e.target.value })}
                placeholder="blockchain-audit"
              />
            </Field>
            <Field label="专家文本 (expert_text)" hint="支持多段 SOP / 政策原文">
              <textarea
                className="input min-h-[16rem] font-mono text-xs"
                value={form.expert_text}
                onChange={(e) =>
                  setForm({ ...form, expert_text: e.target.value })
                }
              />
            </Field>
            <Field label="备注 (notes)">
              <input
                className="input"
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
              />
            </Field>
            <button
              type="button"
              className="btn-primary"
              onClick={onGenerate}
              disabled={generate.isPending}
            >
              {generate.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Wand2 className="h-4 w-4" />
              )}
              {generate.isPending ? '生成中…' : '生成草稿'}
            </button>
          </div>
        </Card>

        <Card>
          <SectionTitle
            title="生成结果"
            description={
              draft
                ? '可在下方修改字段，确认后保存到技能库'
                : '生成后将在此显示结构化 Skill 草稿'
            }
            right={
              editedDraft && (
                <button
                  type="button"
                  className="btn-primary"
                  onClick={onSave}
                  disabled={save.isPending}
                >
                  {save.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  保存技能
                </button>
              )
            }
          />
          {!editedDraft ? (
            <p className="text-sm text-slate-500">尚未生成。</p>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <Field label="ID">
                  <input
                    className="input font-mono"
                    value={editedDraft.id}
                    onChange={(e) =>
                      setEditedDraft({ ...editedDraft, id: e.target.value })
                    }
                  />
                </Field>
                <Field label="名称">
                  <input
                    className="input"
                    value={editedDraft.name}
                    onChange={(e) =>
                      setEditedDraft({ ...editedDraft, name: e.target.value })
                    }
                  />
                </Field>
                <Field label="版本">
                  <input
                    className="input"
                    value={editedDraft.version}
                    onChange={(e) =>
                      setEditedDraft({ ...editedDraft, version: e.target.value })
                    }
                  />
                </Field>
                <Field label="输出 Schema">
                  <input
                    className="input font-mono"
                    value={editedDraft.output_schema}
                    onChange={(e) =>
                      setEditedDraft({
                        ...editedDraft,
                        output_schema: e.target.value,
                      })
                    }
                  />
                </Field>
              </div>
              <Field label="描述">
                <textarea
                  className="input"
                  rows={2}
                  value={editedDraft.description}
                  onChange={(e) =>
                    setEditedDraft({
                      ...editedDraft,
                      description: e.target.value,
                    })
                  }
                />
              </Field>
              <Field label="系统提示">
                <textarea
                  className="input min-h-[8rem] font-mono text-xs"
                  value={editedDraft.system_instruction}
                  onChange={(e) =>
                    setEditedDraft({
                      ...editedDraft,
                      system_instruction: e.target.value,
                    })
                  }
                />
              </Field>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <Field label="允许工具 (每行一项)">
                  <textarea
                    className="input min-h-[6rem] font-mono text-xs"
                    value={editedDraft.allowed_tools.join('\n')}
                    onChange={(e) =>
                      setEditedDraft({
                        ...editedDraft,
                        allowed_tools: e.target.value
                          .split('\n')
                          .map((s) => s.trim())
                          .filter(Boolean),
                      })
                    }
                  />
                </Field>
                <Field label="标签 (逗号分隔)">
                  <input
                    className="input"
                    value={editedDraft.tags.join(', ')}
                    onChange={(e) =>
                      setEditedDraft({
                        ...editedDraft,
                        tags: e.target.value
                          .split(',')
                          .map((s) => s.trim())
                          .filter(Boolean),
                      })
                    }
                  />
                </Field>
                <Field label="风险规则 (每行一条)">
                  <textarea
                    className="input min-h-[6rem]"
                    value={editedDraft.risk_rules.join('\n')}
                    onChange={(e) =>
                      setEditedDraft({
                        ...editedDraft,
                        risk_rules: e.target.value
                          .split('\n')
                          .map((s) => s.trim())
                          .filter(Boolean),
                      })
                    }
                  />
                </Field>
                <Field label="示例 (每行一条)">
                  <textarea
                    className="input min-h-[6rem]"
                    value={editedDraft.examples.join('\n')}
                    onChange={(e) =>
                      setEditedDraft({
                        ...editedDraft,
                        examples: e.target.value
                          .split('\n')
                          .map((s) => s.trim())
                          .filter(Boolean),
                      })
                    }
                  />
                </Field>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {editedDraft.tags.map((t) => (
                  <Tag key={t}>{t}</Tag>
                ))}
              </div>
              {draft?.yaml_preview && (
                <div>
                  <p className="label">YAML 预览</p>
                  <pre className="max-h-72 overflow-auto rounded-lg bg-slate-900 p-3 font-mono text-xs text-slate-100">
                    {draft.yaml_preview}
                  </pre>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
