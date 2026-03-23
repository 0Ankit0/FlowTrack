'use client';

import { useMemo, useState } from 'react';
import { useAuthStore } from '@/store/auth-store';
import { useCreateRelease, useProject, useProjects, useReleases } from '@/hooks/use-flowtrack';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { StatusPill } from '@/components/flowtrack/status-pill';
import { TenantEmptyState } from '@/components/flowtrack/tenant-empty-state';
import type { ReleaseStatus, ReleaseType } from '@/types';

export default function ReleasesPage() {
  const { tenant, user } = useAuthStore();
  const projectsQuery = useProjects(tenant?.id);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const selectedProject = useProject(selectedProjectId || projectsQuery.data?.items?.[0]?.id);
  const releasesQuery = useReleases(tenant?.id, selectedProjectId || undefined);
  const createRelease = useCreateRelease();

  const isInternalUser = useMemo(
    () =>
      Boolean(
        user?.is_superuser ||
          user?.roles.some((role) =>
            ['support', 'project_manager', 'developer', 'qa_reviewer', 'admin'].includes(role)
          )
      ),
    [user]
  );

  const [releaseForm, setReleaseForm] = useState({
    project_id: '',
    milestone_id: '',
    version: '',
    status: 'planned' as ReleaseStatus,
    release_type: 'planned' as ReleaseType,
    notes: '',
  });

  if (!tenant) {
    return (
      <TenantEmptyState
        title="Choose an organization before planning releases"
        description="Release bundles are scoped by organization and project. Select a tenant to coordinate versions, milestones, and linked work items."
      />
    );
  }

  async function handleCreateRelease(e: React.FormEvent) {
    e.preventDefault();
    const projectId = releaseForm.project_id || selectedProjectId || projectsQuery.data?.items?.[0]?.id;
    if (!projectId) return;
    await createRelease.mutateAsync({
      project_id: projectId,
      milestone_id: releaseForm.milestone_id || undefined,
      version: releaseForm.version,
      status: releaseForm.status,
      release_type: releaseForm.release_type,
      notes: releaseForm.notes,
    });
    setReleaseForm({
      project_id: projectId,
      milestone_id: '',
      version: '',
      status: 'planned',
      release_type: 'planned',
      notes: '',
    });
  }

  return (
    <div className="space-y-8">
      <section className="rounded-[30px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_24px_80px_rgba(15,23,42,0.06)]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">Releases</p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">Bundle tickets and tasks into a visible shipping plan</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Plan standard releases and hotfixes, tie them back to milestones, and keep delivery intent explicit for QA and stakeholders.
        </p>
      </section>

      <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <div className="space-y-6">
          <section className="rounded-[28px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_18px_60px_rgba(15,23,42,0.05)]">
            <h2 className="text-2xl font-semibold text-slate-900">Select project</h2>
            <div className="mt-5 space-y-3">
              {(projectsQuery.data?.items ?? []).map((project) => (
                <button
                  key={project.id}
                  type="button"
                  onClick={() => {
                    setSelectedProjectId(project.id);
                    setReleaseForm((current) => ({ ...current, project_id: project.id, milestone_id: '' }));
                  }}
                  className={`w-full rounded-[24px] border p-5 text-left ${
                    (selectedProjectId || projectsQuery.data?.items?.[0]?.id) === project.id
                      ? 'border-transparent bg-[linear-gradient(135deg,rgba(15,118,110,0.14),rgba(190,24,93,0.12))]'
                      : 'border-[rgba(15,23,42,0.08)] bg-[linear-gradient(180deg,#ffffff,#fffaf6)]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <StatusPill value={project.status} />
                    <StatusPill value={project.health} />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-slate-900">{project.name}</h3>
                </button>
              ))}
            </div>
          </section>

          {isInternalUser ? (
            <section className="rounded-[28px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_18px_60px_rgba(15,23,42,0.05)]">
              <h2 className="text-2xl font-semibold text-slate-900">Create release</h2>
              <form className="mt-5 space-y-4" onSubmit={handleCreateRelease}>
                <Input
                  label="Version"
                  value={releaseForm.version}
                  onChange={(e) => setReleaseForm((current) => ({ ...current, version: e.target.value }))}
                  required
                />
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  <span>Milestone</span>
                  <select
                    className="w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                    value={releaseForm.milestone_id}
                    onChange={(e) => setReleaseForm((current) => ({ ...current, milestone_id: e.target.value }))}
                  >
                    <option value="">No milestone</option>
                    {(selectedProject.data?.milestones ?? []).map((milestone) => (
                      <option key={milestone.id} value={milestone.id}>
                        {milestone.name}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="space-y-1 text-sm font-medium text-slate-700">
                    <span>Status</span>
                    <select
                      className="w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                      value={releaseForm.status}
                      onChange={(e) => setReleaseForm((current) => ({ ...current, status: e.target.value as ReleaseStatus }))}
                    >
                      <option value="planned">Planned</option>
                      <option value="in_progress">In progress</option>
                      <option value="deployed">Deployed</option>
                    </select>
                  </label>
                  <label className="space-y-1 text-sm font-medium text-slate-700">
                    <span>Type</span>
                    <select
                      className="w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                      value={releaseForm.release_type}
                      onChange={(e) =>
                        setReleaseForm((current) => ({ ...current, release_type: e.target.value as ReleaseType }))
                      }
                    >
                      <option value="planned">Planned</option>
                      <option value="hotfix">Hotfix</option>
                    </select>
                  </label>
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">Notes</label>
                  <textarea
                    className="min-h-28 w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                    value={releaseForm.notes}
                    onChange={(e) => setReleaseForm((current) => ({ ...current, notes: e.target.value }))}
                  />
                </div>
                <Button type="submit" isLoading={createRelease.isPending}>
                  Create release
                </Button>
              </form>
            </section>
          ) : null}
        </div>

        <section className="rounded-[28px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_18px_60px_rgba(15,23,42,0.05)]">
          <h2 className="text-2xl font-semibold text-slate-900">Release log</h2>
          <div className="mt-5 space-y-4">
            {(releasesQuery.data ?? []).map((release) => (
              <div key={release.id} className="rounded-[24px] border border-[rgba(15,23,42,0.08)] bg-[linear-gradient(180deg,#ffffff,#fffaf6)] p-5">
                <div className="flex flex-wrap items-center gap-3">
                  <StatusPill value={release.status} />
                  <span className="text-xs uppercase tracking-[0.18em] text-slate-400">
                    {release.release_type}
                  </span>
                </div>
                <h3 className="mt-4 text-xl font-semibold text-slate-900">{release.version}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">{release.notes || 'No notes recorded yet.'}</p>
                <div className="mt-4 flex flex-wrap gap-3 text-xs uppercase tracking-[0.18em] text-slate-400">
                  <span>{release.ticket_ids.length} tickets linked</span>
                  <span>{release.task_ids.length} tasks linked</span>
                </div>
              </div>
            ))}
            {(releasesQuery.data ?? []).length === 0 ? (
              <p className="text-sm text-slate-500">No releases recorded yet for this project scope.</p>
            ) : null}
          </div>
        </section>
      </div>
    </div>
  );
}
