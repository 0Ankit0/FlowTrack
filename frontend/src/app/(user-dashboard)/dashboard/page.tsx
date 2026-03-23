'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { ArrowRight, BriefcaseBusiness, FolderKanban, Rocket, Siren, Ticket } from 'lucide-react';
import { useAuthStore } from '@/store/auth-store';
import { useOperationalSummary, useProjects, useReleases, useTickets } from '@/hooks/use-flowtrack';
import { StatusPill } from '@/components/flowtrack/status-pill';
import { TenantEmptyState } from '@/components/flowtrack/tenant-empty-state';

export default function DashboardPage() {
  const { tenant, user } = useAuthStore();
  const summary = useOperationalSummary(tenant?.id);
  const tickets = useTickets({ tenantId: tenant?.id, limit: 6 });
  const projects = useProjects(tenant?.id);
  const releases = useReleases(tenant?.id);

  const stats = useMemo(
    () =>
      summary.data
        ? [
            {
              name: 'Open Tickets',
              value: String(summary.data.open_ticket_count),
              detail: 'Across active queues',
              icon: Ticket,
            },
            {
              name: 'SLA Risk',
              value: String(summary.data.breached_ticket_count),
              detail: 'Breached or overdue',
              icon: Siren,
            },
            {
              name: 'Active Projects',
              value: String(summary.data.active_project_count),
              detail: `${summary.data.project_count} total tracked`,
              icon: FolderKanban,
            },
            {
              name: 'Milestone Pace',
              value: `${Math.round(summary.data.milestone_completion_rate * 100)}%`,
              detail: 'Completed checkpoints',
              icon: Rocket,
            },
          ]
        : [],
    [summary.data]
  );

  if (!tenant) {
    return (
      <TenantEmptyState
        title="Choose an organization to enter Flowtrack"
        description="Flowtrack is tenant-scoped. Pick an organization from the switcher on the left to view its live tickets, active projects, releases, and workload metrics."
      />
    );
  }

  return (
    <div className="space-y-8">
      <section className="overflow-hidden rounded-[32px] border border-[rgba(15,23,42,0.08)] bg-[linear-gradient(135deg,#082f49_0%,#134e4a_38%,#881337_100%)] p-8 text-white shadow-[0_30px_100px_rgba(8,47,73,0.25)]">
        <div className="grid gap-8 lg:grid-cols-[1.8fr_1fr]">
          <div className="space-y-5">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-white/80">
              <BriefcaseBusiness className="h-3.5 w-3.5" />
              {tenant.name}
            </div>
            <div className="space-y-3">
              <h1 className="max-w-3xl font-serif text-4xl leading-tight md:text-5xl">
                Ship work without losing the thread between ticket queues and delivery plans.
              </h1>
              <p className="max-w-2xl text-sm leading-7 text-white/80">
                Flowtrack keeps client issues, project milestones, and release readiness in one
                operating picture for support, PMs, developers, and QA.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/tickets"
                className="inline-flex items-center gap-2 rounded-full bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition-transform hover:-translate-y-0.5"
              >
                Open ticket queue
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/projects"
                className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/15"
              >
                Review milestones
              </Link>
            </div>
          </div>

          <div className="rounded-[28px] border border-white/12 bg-white/8 p-5 backdrop-blur-sm">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-white/65">
              Workload Snapshot
            </p>
            <div className="mt-4 space-y-4">
              {Object.entries(summary.data?.workload_by_assignee ?? {}).slice(0, 4).map(([id, count]) => (
                <div key={id} className="space-y-1">
                  <div className="flex items-center justify-between text-sm text-white/85">
                    <span>Assignee {id.slice(0, 6)}</span>
                    <span>{count} open</span>
                  </div>
                  <div className="h-2 rounded-full bg-white/10">
                    <div
                      className="h-2 rounded-full bg-[linear-gradient(90deg,#f59e0b,#fb7185)]"
                      style={{ width: `${Math.min(count * 18, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
              {!summary.data?.workload_by_assignee ||
              Object.keys(summary.data.workload_by_assignee).length === 0 ? (
                <p className="text-sm text-white/65">No active assignees yet for this organization.</p>
              ) : null}
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="rounded-[28px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_20px_60px_rgba(15,23,42,0.05)]"
          >
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                {stat.name}
              </p>
              <div className="rounded-2xl bg-[linear-gradient(135deg,rgba(20,184,166,0.12),rgba(190,24,93,0.12))] p-3 text-slate-700">
                <stat.icon className="h-4 w-4" />
              </div>
            </div>
            <p className="mt-5 text-4xl font-semibold text-slate-900">{stat.value}</p>
            <p className="mt-2 text-sm text-slate-500">{stat.detail}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <section className="rounded-[30px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_24px_80px_rgba(15,23,42,0.06)]">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                Ticket Queue
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-900">Latest activity</h2>
            </div>
            <Link href="/tickets" className="text-sm font-semibold text-teal-700 hover:text-teal-800">
              View all
            </Link>
          </div>
          <div className="mt-6 space-y-4">
            {(tickets.data?.items ?? []).map((ticket) => (
              <div
                key={ticket.id}
                className="rounded-[24px] border border-[rgba(15,23,42,0.07)] bg-[linear-gradient(180deg,#fffefb,#fff8f3)] p-5"
              >
                <div className="flex flex-wrap items-center gap-3">
                  <StatusPill value={ticket.status} />
                  <StatusPill value={ticket.priority} />
                  <span className="text-xs uppercase tracking-[0.22em] text-slate-400">
                    {ticket.type.replace(/_/g, ' ')}
                  </span>
                </div>
                <h3 className="mt-4 text-lg font-semibold text-slate-900">{ticket.title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">{ticket.description}</p>
                <div className="mt-4 flex flex-wrap items-center gap-4 text-xs uppercase tracking-[0.18em] text-slate-400">
                  <span>Created {new Date(ticket.created_at).toLocaleDateString()}</span>
                  <span>{ticket.severity}</span>
                  {ticket.project_id ? <span>Linked project</span> : <span>Unlinked ticket</span>}
                </div>
              </div>
            ))}
            {tickets.data?.items.length === 0 ? (
              <p className="rounded-[20px] border border-dashed border-[rgba(15,23,42,0.12)] px-5 py-6 text-sm text-slate-500">
                No tickets yet. Start from the tickets page to log the first incoming request for this organization.
              </p>
            ) : null}
          </div>
        </section>

        <section className="space-y-6">
          <div className="rounded-[30px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_24px_80px_rgba(15,23,42,0.06)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                  Projects
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-900">Portfolio pulse</h2>
              </div>
              <Link href="/projects" className="text-sm font-semibold text-teal-700 hover:text-teal-800">
                Explore
              </Link>
            </div>
            <div className="mt-5 space-y-4">
              {(projects.data?.items ?? []).slice(0, 3).map((project) => (
                <div key={project.id} className="rounded-[22px] border border-[rgba(15,23,42,0.07)] p-4">
                  <div className="flex items-center gap-3">
                    <StatusPill value={project.status} />
                    <StatusPill value={project.health} />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-slate-900">{project.name}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{project.description}</p>
                </div>
              ))}
              {projects.data?.items.length === 0 ? (
                <p className="text-sm text-slate-500">No projects have been created for this organization yet.</p>
              ) : null}
            </div>
          </div>

          <div className="rounded-[30px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_24px_80px_rgba(15,23,42,0.06)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                  Releases
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-900">Shipping rhythm</h2>
              </div>
              <Link href="/releases" className="text-sm font-semibold text-teal-700 hover:text-teal-800">
                Manage
              </Link>
            </div>
            <div className="mt-5 space-y-4">
              {(releases.data ?? []).slice(0, 3).map((release) => (
                <div key={release.id} className="rounded-[22px] border border-[rgba(15,23,42,0.07)] p-4">
                  <div className="flex items-center gap-3">
                    <StatusPill value={release.status} />
                    <span className="text-xs uppercase tracking-[0.18em] text-slate-400">
                      {release.release_type}
                    </span>
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-slate-900">{release.version}</h3>
                  <p className="mt-2 text-sm text-slate-600">
                    {release.notes || 'No release notes recorded yet.'}
                  </p>
                </div>
              ))}
              {(releases.data ?? []).length === 0 ? (
                <p className="text-sm text-slate-500">No releases are planned yet for this workspace.</p>
              ) : null}
            </div>
          </div>
        </section>
      </div>

      {!user?.is_confirmed ? (
        <div className="rounded-[26px] border border-[rgba(217,119,6,0.18)] bg-[rgba(251,191,36,0.12)] p-5 text-sm text-amber-900">
          Verify your email to keep internal and client communication fully traceable inside Flowtrack.
        </div>
      ) : null}
    </div>
  );
}
