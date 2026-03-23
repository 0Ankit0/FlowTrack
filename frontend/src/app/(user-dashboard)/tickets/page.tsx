'use client';

import { useEffect, useMemo, useState } from 'react';
import { useAuthStore } from '@/store/auth-store';
import { useAssignTicket, useCreateTicket, useProjects, useRegisterTicketAttachment, useTicket, useTickets, useUpdateTicket, useAddTicketComment } from '@/hooks/use-flowtrack';
import { useListUsers } from '@/hooks/use-users';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { StatusPill } from '@/components/flowtrack/status-pill';
import { TenantEmptyState } from '@/components/flowtrack/tenant-empty-state';
import type { CommentVisibility, TicketPriority, TicketSeverity, TicketStatus, TicketType } from '@/types';

const ticketStatuses: TicketStatus[] = [
  'new',
  'awaiting_clarification',
  'triaged',
  'assigned',
  'in_progress',
  'blocked',
  'ready_for_qa',
  'closed',
  'reopened',
];

export default function TicketsPage() {
  const { tenant, user } = useAuthStore();
  const tenantId = tenant?.id;
  const ticketsQuery = useTickets({ tenantId, limit: 50 });
  const projectsQuery = useProjects(tenantId);
  const usersQuery = useListUsers({ limit: 100 });
  const createTicket = useCreateTicket();
  const updateTicket = useUpdateTicket();
  const addComment = useAddTicketComment();
  const registerAttachment = useRegisterTicketAttachment();
  const assignTicket = useAssignTicket();

  const [selectedTicketId, setSelectedTicketId] = useState<string>();
  const ticketDetail = useTicket(selectedTicketId);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

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

  const [ticketForm, setTicketForm] = useState<{
    title: string;
    description: string;
    category: string;
    environment: string;
    type: TicketType;
    severity: TicketSeverity;
    priority: TicketPriority;
    project_id: string;
  }>({
    title: '',
    description: '',
    category: '',
    environment: 'production',
    type: 'bug',
    severity: 'medium',
    priority: 'P3',
    project_id: '',
  });

  const [commentForm, setCommentForm] = useState({ body: '', visibility: 'public' as CommentVisibility });
  const [assignmentForm, setAssignmentForm] = useState({ assignee_id: '', note: '' });

  useEffect(() => {
    if (!selectedTicketId && ticketsQuery.data?.items?.length) {
      setSelectedTicketId(ticketsQuery.data.items[0].id);
    }
  }, [selectedTicketId, ticketsQuery.data?.items]);

  if (!tenant) {
    return (
      <TenantEmptyState
        title="Select an organization before opening the ticket queue"
        description="Tickets are scoped by organization. Choose a tenant from the left sidebar to create, triage, and track requests in the correct client workspace."
      />
    );
  }

  async function handleCreateTicket(e: React.FormEvent) {
    e.preventDefault();
    if (!tenantId) return;
    const ticket = await createTicket.mutateAsync({
      tenant_id: tenantId,
      title: ticketForm.title,
      description: ticketForm.description,
      category: ticketForm.category,
      environment: ticketForm.environment,
      type: ticketForm.type,
      severity: ticketForm.severity,
      priority: ticketForm.priority,
      project_id: ticketForm.project_id || undefined,
    });

    if (selectedFile) {
      await registerAttachment.mutateAsync({
        ticketId: ticket.id,
        payload: {
          filename: selectedFile.name,
          mime_type: selectedFile.type,
          size_bytes: selectedFile.size,
          storage_key: `tickets/${Date.now()}-${selectedFile.name}`,
        },
      });
      setSelectedFile(null);
    }

    setSelectedTicketId(ticket.id);
    setTicketForm({
      title: '',
      description: '',
      category: '',
      environment: 'production',
      type: 'bug',
      severity: 'medium',
      priority: 'P3',
      project_id: '',
    });
  }

  async function handleAddComment(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedTicketId || !commentForm.body.trim()) return;
    await addComment.mutateAsync({ ticketId: selectedTicketId, payload: commentForm });
    setCommentForm({ body: '', visibility: isInternalUser ? commentForm.visibility : 'public' });
  }

  async function handleAssignTicket(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedTicketId || !assignmentForm.assignee_id) return;
    await assignTicket.mutateAsync({
      ticketId: selectedTicketId,
      payload: assignmentForm,
    });
    setAssignmentForm({ assignee_id: '', note: '' });
  }

  return (
    <div className="space-y-8">
      <section className="rounded-[30px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_24px_80px_rgba(15,23,42,0.06)]">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
              Ticketing
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-900">Client intake and delivery queue</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              Submit tickets with evidence, keep the queue triaged, and move work cleanly through clarification, assignment, QA, and closure.
            </p>
          </div>
          <div className="rounded-full border border-[rgba(15,23,42,0.08)] bg-[rgba(15,23,42,0.03)] px-4 py-2 text-xs uppercase tracking-[0.2em] text-slate-500">
            {ticketsQuery.data?.total ?? 0} tickets in scope
          </div>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-6">
          <section className="rounded-[28px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_18px_60px_rgba(15,23,42,0.05)]">
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                Create Ticket
              </p>
              <h2 className="text-2xl font-semibold text-slate-900">Log a new request</h2>
            </div>
            <form className="mt-5 space-y-4" onSubmit={handleCreateTicket}>
              <Input
                label="Title"
                value={ticketForm.title}
                onChange={(e) => setTicketForm((current) => ({ ...current, title: e.target.value }))}
                required
              />
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Description</label>
                <textarea
                  className="min-h-32 w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  value={ticketForm.description}
                  onChange={(e) => setTicketForm((current) => ({ ...current, description: e.target.value }))}
                  required
                />
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <Input
                  label="Category"
                  value={ticketForm.category}
                  onChange={(e) => setTicketForm((current) => ({ ...current, category: e.target.value }))}
                />
                <Input
                  label="Environment"
                  value={ticketForm.environment}
                  onChange={(e) => setTicketForm((current) => ({ ...current, environment: e.target.value }))}
                />
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  <span>Type</span>
                  <select
                    className="w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                    value={ticketForm.type}
                    onChange={(e) => setTicketForm((current) => ({ ...current, type: e.target.value as TicketType }))}
                  >
                    <option value="bug">Bug</option>
                    <option value="incident">Incident</option>
                    <option value="service_request">Service request</option>
                    <option value="change_request">Change request</option>
                  </select>
                </label>
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  <span>Severity</span>
                  <select
                    className="w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                    value={ticketForm.severity}
                    onChange={(e) =>
                      setTicketForm((current) => ({ ...current, severity: e.target.value as TicketSeverity }))
                    }
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </label>
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  <span>Priority</span>
                  <select
                    className="w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                    value={ticketForm.priority}
                    onChange={(e) =>
                      setTicketForm((current) => ({ ...current, priority: e.target.value as TicketPriority }))
                    }
                  >
                    <option value="P1">P1</option>
                    <option value="P2">P2</option>
                    <option value="P3">P3</option>
                    <option value="P4">P4</option>
                  </select>
                </label>
              </div>
              <label className="space-y-1 text-sm font-medium text-slate-700">
                <span>Project link</span>
                <select
                  className="w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                  value={ticketForm.project_id}
                  onChange={(e) => setTicketForm((current) => ({ ...current, project_id: e.target.value }))}
                >
                  <option value="">No project yet</option>
                  {(projectsQuery.data?.items ?? []).map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
              </label>
              <div className="space-y-1">
                <label className="block text-sm font-medium text-slate-700">Evidence image</label>
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp,image/gif"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
                  className="block w-full text-sm text-slate-600"
                />
                <p className="text-xs text-slate-400">Supported: PNG, JPG, WEBP, GIF up to 10 MB.</p>
              </div>
              <Button type="submit" isLoading={createTicket.isPending}>
                Create ticket
              </Button>
            </form>
          </section>

          <section className="rounded-[28px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_18px_60px_rgba(15,23,42,0.05)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                  Queue
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-900">Current tickets</h2>
              </div>
            </div>
            <div className="mt-5 space-y-3">
              {(ticketsQuery.data?.items ?? []).map((ticket) => (
                <button
                  key={ticket.id}
                  type="button"
                  onClick={() => setSelectedTicketId(ticket.id)}
                  className={`w-full rounded-[24px] border p-5 text-left transition-all ${
                    selectedTicketId === ticket.id
                      ? 'border-transparent bg-[linear-gradient(135deg,rgba(15,118,110,0.14),rgba(190,24,93,0.12))] shadow-[0_18px_50px_rgba(15,23,42,0.08)]'
                      : 'border-[rgba(15,23,42,0.08)] bg-[linear-gradient(180deg,#ffffff,#fffaf6)] hover:border-[rgba(15,118,110,0.25)]'
                  }`}
                >
                  <div className="flex flex-wrap items-center gap-3">
                    <StatusPill value={ticket.status} />
                    <StatusPill value={ticket.priority} />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-slate-900">{ticket.title}</h3>
                  <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-600">
                    {ticket.description}
                  </p>
                </button>
              ))}
            </div>
          </section>
        </div>

        <section className="rounded-[28px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_18px_60px_rgba(15,23,42,0.05)]">
          {!ticketDetail.data ? (
            <p className="text-sm text-slate-500">Select a ticket to inspect its activity, assignments, and evidence.</p>
          ) : (
            <div className="space-y-6">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-3">
                  <StatusPill value={ticketDetail.data.status} />
                  <StatusPill value={ticketDetail.data.priority} />
                </div>
                <h2 className="text-3xl font-semibold text-slate-900">{ticketDetail.data.title}</h2>
                <p className="text-sm leading-7 text-slate-600">{ticketDetail.data.description}</p>
              </div>

              {isInternalUser ? (
                <div className="grid gap-4 rounded-[24px] border border-[rgba(15,23,42,0.08)] bg-[rgba(15,23,42,0.03)] p-5 md:grid-cols-2">
                  <label className="space-y-1 text-sm font-medium text-slate-700">
                    <span>Status</span>
                    <select
                      className="w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                      value={ticketDetail.data.status}
                      onChange={(e) =>
                        updateTicket.mutate({
                          ticketId: ticketDetail.data.id,
                          payload: { status: e.target.value as TicketStatus },
                        })
                      }
                    >
                      {ticketStatuses.map((status) => (
                        <option key={status} value={status}>
                          {status.replace(/_/g, ' ')}
                        </option>
                      ))}
                    </select>
                  </label>
                  <form className="space-y-3" onSubmit={handleAssignTicket}>
                    <label className="space-y-1 text-sm font-medium text-slate-700">
                      <span>Assign owner</span>
                      <select
                        className="w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm"
                        value={assignmentForm.assignee_id}
                        onChange={(e) =>
                          setAssignmentForm((current) => ({ ...current, assignee_id: e.target.value }))
                        }
                      >
                        <option value="">Select assignee</option>
                        {(usersQuery.data?.items ?? []).map((assignee) => (
                          <option key={assignee.id} value={assignee.id}>
                            {assignee.first_name || assignee.username || assignee.email}
                          </option>
                        ))}
                      </select>
                    </label>
                    <Input
                      label="Assignment note"
                      value={assignmentForm.note}
                      onChange={(e) => setAssignmentForm((current) => ({ ...current, note: e.target.value }))}
                    />
                    <Button type="submit" size="sm" isLoading={assignTicket.isPending}>
                      Assign
                    </Button>
                  </form>
                </div>
              ) : null}

              <div className="grid gap-6 lg:grid-cols-2">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                    Comments
                  </p>
                  <div className="mt-4 space-y-3">
                    {ticketDetail.data.comments.map((comment) => (
                      <div key={comment.id} className="rounded-[20px] border border-[rgba(15,23,42,0.07)] p-4">
                        <div className="flex items-center gap-3">
                          <StatusPill value={comment.visibility} />
                          <span className="text-xs uppercase tracking-[0.18em] text-slate-400">
                            {new Date(comment.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="mt-3 text-sm leading-6 text-slate-700">{comment.body}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                    Attachments & assignments
                  </p>
                  <div className="mt-4 space-y-3">
                    {ticketDetail.data.attachments.map((attachment) => (
                      <div key={attachment.id} className="rounded-[20px] border border-[rgba(15,23,42,0.07)] p-4 text-sm text-slate-700">
                        <div className="flex items-center gap-3">
                          <StatusPill value={attachment.scan_status} />
                          <span className="font-semibold">{attachment.filename}</span>
                        </div>
                        <p className="mt-2 text-xs text-slate-500">
                          {attachment.mime_type} • {(attachment.size_bytes / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    ))}
                    {ticketDetail.data.assignments.map((assignment) => (
                      <div key={assignment.id} className="rounded-[20px] border border-[rgba(15,23,42,0.07)] p-4 text-sm text-slate-700">
                        Assigned to {assignment.assignee_id} on{' '}
                        {new Date(assignment.assigned_at).toLocaleString()}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <form className="space-y-4 rounded-[24px] border border-[rgba(15,23,42,0.08)] bg-[rgba(15,23,42,0.03)] p-5" onSubmit={handleAddComment}>
                <div className="flex items-center justify-between">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                    Add comment
                  </p>
                  {isInternalUser ? (
                    <select
                      className="rounded-full border border-gray-300 px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em]"
                      value={commentForm.visibility}
                      onChange={(e) =>
                        setCommentForm((current) => ({
                          ...current,
                          visibility: e.target.value as CommentVisibility,
                        }))
                      }
                    >
                      <option value="public">Public</option>
                      <option value="internal">Internal</option>
                    </select>
                  ) : null}
                </div>
                <textarea
                  className="min-h-28 w-full rounded-2xl border border-gray-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  value={commentForm.body}
                  onChange={(e) => setCommentForm((current) => ({ ...current, body: e.target.value }))}
                />
                <Button type="submit" size="sm" isLoading={addComment.isPending}>
                  Post comment
                </Button>
              </form>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
