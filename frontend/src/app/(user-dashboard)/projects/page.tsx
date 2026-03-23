'use client';

import { useEffect, useMemo, useState } from 'react';
import { useAuthStore } from '@/store/auth-store';
import { useCreateMilestone, useCreateProject, useCreateTask, useProject, useProjects, useTickets } from '@/hooks/use-flowtrack';
import { useListUsers } from '@/hooks/use-users';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { StatusPill } from '@/components/flowtrack/status-pill';
import { TenantEmptyState } from '@/components/flowtrack/tenant-empty-state';
import type { MilestoneStatus, ProjectHealth, ProjectStatus, TaskStatus } from '@/types';

export default function ProjectsPage() {
  const { tenant, user } = useAuthStore();
  const tenantId = tenant?.id;
  const projectsQuery = useProjects(tenantId);
  const createProject = useCreateProject();
  const createMilestone = useCreateMilestone();
  const createTask = useCreateTask();
  const usersQuery = useListUsers({ limit: 100 });
  const ticketsQuery = useTickets({ tenantId, limit: 100 });
  const [selectedProjectId, setSelectedProjectId] = useState<string>();
  const projectDetail = useProject(selectedProjectId);

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

  const [projectForm, setProjectForm] = useState({
    name: '',
    description: '',
    status: 'active' as ProjectStatus,
    health: 'green' as ProjectHealth,
  });
  const [milestoneForm, setMilestoneForm] = useState({
    name: '',
    planned_date: '',
    status: 'draft' as MilestoneStatus,
    completion_criteria: '',
  });
  const [taskForm, setTaskForm] = useState({
    title: '',
    description: '',
    assignee_id: '',
    linked_ticket_id: '',
    status: 'todo' as TaskStatus,
  });

  useEffect(() => {
    if (!selectedProjectId && projectsQuery.data?.items?.length) {
      setSelectedProjectId(projectsQuery.data.items[0].id);
    }
  }, [projectsQuery.data?.items, selectedProjectId]);

  if (!tenant) {
    return (
      <TenantEmptyState
        title="Select an organization to manage projects"
        description="Project plans, milestones, and tasks are organization-scoped. Choose the client workspace you want to plan against."
      />
    );
  }

  async function handleCreateProject(e: React.FormEvent) {
    e.preventDefault();
    if (!tenantId) return;
    const project = await createProject.mutateAsync({
      tenant_id: tenantId,
      name: projectForm.name,
      description: projectForm.description,
      status: projectForm.status,
      health: projectForm.health,
    });
    setSelectedProjectId(project.id);
    setProjectForm({ name: '', description: '', status: 'active', health: 'green' });
  }

  async function handleCreateMilestone(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedProjectId) return;
    await createMilestone.mutateAsync({
      projectId: selectedProjectId,
      payload: {
        name: milestoneForm.name,
        planned_date: milestoneForm.planned_date,
        status: milestoneForm.status,
        completion_criteria: milestoneForm.completion_criteria
          .split('\n')
          .map((item) => item.trim())
          .filter(Boolean),
      },
    });
    setMilestoneForm({ name: '', planned_date: '', status: 'draft', completion_criteria: '' });
  }

  async function handleCreateTask(e: React.FormEvent) {
    e.preventDefault();
    const milestoneId = projectDetail.data?.milestones?.[0]?.id;
    if (!milestoneId) return;
    await createTask.mutateAsync({
      milestoneId,
      payload: {
        title: taskForm.title,
        description: taskForm.description,
        assignee_id: taskForm.assignee_id || undefined,
        linked_ticket_id: taskForm.linked_ticket_id || undefined,
        status: taskForm.status,
      },
    });
    setTaskForm({ title: '', description: '', assignee_id: '', linked_ticket_id: '', status: 'todo' });
  }

  return (
    <div className="space-y-8">
      <section className="rounded-[30px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_24px_80px_rgba(15,23,42,0.06)]">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
              Project Delivery
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-900">Plan milestones beside live issue volume</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              Keep delivery governance in the same workspace as ticket intake so milestones, dependencies, and blockers stay visible end to end.
            </p>
          </div>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-6">
          {isInternalUser ? (
            <section className="rounded-[28px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_18px_60px_rgba(15,23,42,0.05)]">
              <h2 className="text-2xl font-semibold text-slate-900">Create project</h2>
              <form className="mt-5 space-y-4" onSubmit={handleCreateProject}>
                <Input
                  label="Project name"
                  value={projectForm.name}
                  onChange={(e) => setProjectForm((current) => ({ ...current, name: e.target.value }))}
                  required
                />
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">Description</label>
                  <textarea
                    className="min-h-28 w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                    value={projectForm.description}
                    onChange={(e) =>
                      setProjectForm((current) => ({ ...current, description: e.target.value }))
                    }
                  />
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="space-y-1 text-sm font-medium text-slate-700">
                    <span>Status</span>
                    <select
                      className="w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                      value={projectForm.status}
                      onChange={(e) =>
                        setProjectForm((current) => ({ ...current, status: e.target.value as ProjectStatus }))
                      }
                    >
                      <option value="active">Active</option>
                      <option value="draft">Draft</option>
                      <option value="on_hold">On hold</option>
                    </select>
                  </label>
                  <label className="space-y-1 text-sm font-medium text-slate-700">
                    <span>Health</span>
                    <select
                      className="w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                      value={projectForm.health}
                      onChange={(e) =>
                        setProjectForm((current) => ({ ...current, health: e.target.value as ProjectHealth }))
                      }
                    >
                      <option value="green">Green</option>
                      <option value="amber">Amber</option>
                      <option value="red">Red</option>
                    </select>
                  </label>
                </div>
                <Button type="submit" isLoading={createProject.isPending}>
                  Create project
                </Button>
              </form>
            </section>
          ) : null}

          <section className="rounded-[28px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_18px_60px_rgba(15,23,42,0.05)]">
            <h2 className="text-2xl font-semibold text-slate-900">Projects</h2>
            <div className="mt-5 space-y-3">
              {(projectsQuery.data?.items ?? []).map((project) => (
                <button
                  key={project.id}
                  type="button"
                  onClick={() => setSelectedProjectId(project.id)}
                  className={`w-full rounded-[24px] border p-5 text-left transition-all ${
                    selectedProjectId === project.id
                      ? 'border-transparent bg-[linear-gradient(135deg,rgba(15,118,110,0.14),rgba(190,24,93,0.12))]'
                      : 'border-[rgba(15,23,42,0.08)] bg-[linear-gradient(180deg,#ffffff,#fffaf6)]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <StatusPill value={project.status} />
                    <StatusPill value={project.health} />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-slate-900">{project.name}</h3>
                  <p className="mt-2 text-sm text-slate-600">{project.description}</p>
                </button>
              ))}
            </div>
          </section>
        </div>

        <section className="rounded-[28px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_18px_60px_rgba(15,23,42,0.05)]">
          {!projectDetail.data ? (
            <p className="text-sm text-slate-500">Select a project to inspect milestones, tasks, and linked release work.</p>
          ) : (
            <div className="space-y-6">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <StatusPill value={projectDetail.data.status} />
                  <StatusPill value={projectDetail.data.health} />
                </div>
                <h2 className="text-3xl font-semibold text-slate-900">{projectDetail.data.name}</h2>
                <p className="text-sm leading-7 text-slate-600">{projectDetail.data.description}</p>
              </div>

              {isInternalUser ? (
                <div className="grid gap-6 lg:grid-cols-2">
                  <form className="space-y-4 rounded-[24px] border border-[rgba(15,23,42,0.08)] p-5" onSubmit={handleCreateMilestone}>
                    <h3 className="text-lg font-semibold text-slate-900">Add milestone</h3>
                    <Input
                      label="Milestone name"
                      value={milestoneForm.name}
                      onChange={(e) => setMilestoneForm((current) => ({ ...current, name: e.target.value }))}
                    />
                    <Input
                      label="Planned date"
                      type="date"
                      value={milestoneForm.planned_date}
                      onChange={(e) =>
                        setMilestoneForm((current) => ({ ...current, planned_date: e.target.value }))
                      }
                    />
                    <label className="space-y-1 text-sm font-medium text-slate-700">
                      <span>Status</span>
                      <select
                        className="w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                        value={milestoneForm.status}
                        onChange={(e) =>
                          setMilestoneForm((current) => ({ ...current, status: e.target.value as MilestoneStatus }))
                        }
                      >
                        <option value="draft">Draft</option>
                        <option value="baselined">Baselined</option>
                        <option value="in_progress">In progress</option>
                      </select>
                    </label>
                    <div>
                      <label className="mb-1 block text-sm font-medium text-slate-700">
                        Completion criteria
                      </label>
                      <textarea
                        className="min-h-24 w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                        value={milestoneForm.completion_criteria}
                        onChange={(e) =>
                          setMilestoneForm((current) => ({
                            ...current,
                            completion_criteria: e.target.value,
                          }))
                        }
                      />
                    </div>
                    <Button type="submit" size="sm" isLoading={createMilestone.isPending}>
                      Create milestone
                    </Button>
                  </form>

                  <form className="space-y-4 rounded-[24px] border border-[rgba(15,23,42,0.08)] p-5" onSubmit={handleCreateTask}>
                    <h3 className="text-lg font-semibold text-slate-900">Add task</h3>
                    <Input
                      label="Task title"
                      value={taskForm.title}
                      onChange={(e) => setTaskForm((current) => ({ ...current, title: e.target.value }))}
                    />
                    <Input
                      label="Task description"
                      value={taskForm.description}
                      onChange={(e) => setTaskForm((current) => ({ ...current, description: e.target.value }))}
                    />
                    <label className="space-y-1 text-sm font-medium text-slate-700">
                      <span>Assignee</span>
                      <select
                        className="w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                        value={taskForm.assignee_id}
                        onChange={(e) =>
                          setTaskForm((current) => ({ ...current, assignee_id: e.target.value }))
                        }
                      >
                        <option value="">No assignee</option>
                        {(usersQuery.data?.items ?? []).map((assignee) => (
                          <option key={assignee.id} value={assignee.id}>
                            {assignee.first_name || assignee.username || assignee.email}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="space-y-1 text-sm font-medium text-slate-700">
                      <span>Linked ticket</span>
                      <select
                        className="w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                        value={taskForm.linked_ticket_id}
                        onChange={(e) =>
                          setTaskForm((current) => ({ ...current, linked_ticket_id: e.target.value }))
                        }
                      >
                        <option value="">No ticket link</option>
                        {(ticketsQuery.data?.items ?? []).map((ticket) => (
                          <option key={ticket.id} value={ticket.id}>
                            {ticket.title}
                          </option>
                        ))}
                      </select>
                    </label>
                    <Button type="submit" size="sm" isLoading={createTask.isPending}>
                      Create task
                    </Button>
                  </form>
                </div>
              ) : null}

              <div className="grid gap-6 lg:grid-cols-2">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">Milestones</p>
                  <div className="mt-4 space-y-3">
                    {projectDetail.data.milestones.map((milestone) => (
                      <div key={milestone.id} className="rounded-[20px] border border-[rgba(15,23,42,0.07)] p-4">
                        <div className="flex items-center gap-3">
                          <StatusPill value={milestone.status} />
                          <span className="text-xs uppercase tracking-[0.18em] text-slate-400">
                            {milestone.planned_date}
                          </span>
                        </div>
                        <h3 className="mt-3 text-lg font-semibold text-slate-900">{milestone.name}</h3>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {milestone.completion_criteria.map((criterion) => (
                            <span key={criterion} className="rounded-full bg-[rgba(15,23,42,0.05)] px-3 py-1 text-xs text-slate-600">
                              {criterion}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">Tasks</p>
                  <div className="mt-4 space-y-3">
                    {projectDetail.data.tasks.map((task) => (
                      <div key={task.id} className="rounded-[20px] border border-[rgba(15,23,42,0.07)] p-4">
                        <div className="flex items-center gap-3">
                          <StatusPill value={task.status} />
                        </div>
                        <h3 className="mt-3 text-lg font-semibold text-slate-900">{task.title}</h3>
                        <p className="mt-2 text-sm text-slate-600">{task.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
