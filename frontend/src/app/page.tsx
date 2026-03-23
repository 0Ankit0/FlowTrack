'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { FolderKanban, Rocket, Shield, Ticket } from 'lucide-react';

const features = [
  {
    icon: Ticket,
    title: 'Client Ticket Portal',
    description: 'External users can log issues, attach evidence, and follow the response trail without seeing internal-only workflow data.',
  },
  {
    icon: FolderKanban,
    title: 'Project Delivery Control',
    description: 'Projects, milestones, tasks, blockers, and linked tickets stay in one shared operating picture.',
  },
  {
    icon: Rocket,
    title: 'Release Planning',
    description: 'Bundle milestone work into planned releases and hotfixes with traceable links back to tickets and tasks.',
  },
  {
    icon: Shield,
    title: 'Tenant-Scoped Access',
    description: 'Role-aware access keeps each organization isolated while support, PM, QA, and engineering collaborate internally.',
  },
];

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(20,184,166,0.12),transparent_24%),radial-gradient(circle_at_bottom_right,rgba(190,24,93,0.12),transparent_22%),linear-gradient(180deg,#fff8ef_0%,#fffef9_44%,#f8fafc_100%)]">
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-[rgba(15,23,42,0.08)] bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-6">
          <div className="inline-flex items-center gap-3 rounded-full border border-[rgba(15,23,42,0.08)] bg-white px-4 py-2 shadow-[0_14px_40px_rgba(15,23,42,0.05)]">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[linear-gradient(135deg,#0f766e,#be185d)] text-[11px] font-black uppercase tracking-[0.18em] text-white">
              FT
            </span>
            <span className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-800">Flowtrack</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost">Sign in</Button>
            </Link>
            <Link href="/signup">
              <Button>Enter workspace</Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="pt-24">
        <section className="px-6 py-20">
          <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[1.15fr_0.85fr]">
            <div className="space-y-8">
              <div className="inline-flex items-center gap-2 rounded-full border border-[rgba(15,23,42,0.08)] bg-white px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500 shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
                Internal delivery + external support
              </div>
              <div className="space-y-5">
                <h1 className="max-w-4xl font-serif text-5xl leading-tight text-slate-950 md:text-6xl">
                  Flow work from client report to milestone completion without context switching.
                </h1>
                <p className="max-w-2xl text-lg leading-8 text-slate-600">
                  Flowtrack combines external ticket intake with internal project planning, assignment,
                  QA, and release coordination so teams can ship fixes and delivery milestones from one place.
                </p>
              </div>
              <div className="flex flex-col gap-4 sm:flex-row">
                <Link href="/signup">
                  <Button size="lg" className="w-full sm:w-auto">
                    Create account
                  </Button>
                </Link>
                <Link href="/login">
                  <Button variant="outline" size="lg" className="w-full sm:w-auto">
                    Open existing workspace
                  </Button>
                </Link>
              </div>
            </div>

            <div className="rounded-[34px] border border-[rgba(15,23,42,0.08)] bg-[linear-gradient(160deg,#082f49,#0f766e_45%,#881337)] p-6 text-white shadow-[0_28px_90px_rgba(8,47,73,0.28)]">
              <div className="rounded-[28px] border border-white/12 bg-white/8 p-5 backdrop-blur-sm">
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-white/65">
                  Live Operations
                </p>
                <div className="mt-5 grid gap-4 sm:grid-cols-2">
                  {[
                    ['P1 / P2 queue', 'Urgent work stays visible'],
                    ['Milestones', 'Plans and blockers stay linked'],
                    ['Releases', 'Ship bundles with traceability'],
                    ['Audit trail', 'Every workflow change is recorded'],
                  ].map(([title, text]) => (
                    <div key={title} className="rounded-[22px] border border-white/10 bg-white/8 p-4">
                      <p className="text-sm font-semibold text-white">{title}</p>
                      <p className="mt-2 text-sm leading-6 text-white/72">{text}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="px-6 py-16">
          <div className="mx-auto max-w-7xl">
            <div className="mb-10 flex items-end justify-between gap-4">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                  Core Surfaces
                </p>
                <h2 className="mt-2 text-3xl font-semibold text-slate-950">Everything your delivery team needs</h2>
              </div>
            </div>
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="rounded-[28px] border border-[rgba(15,23,42,0.08)] bg-white p-6 shadow-[0_20px_60px_rgba(15,23,42,0.05)]"
                >
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,rgba(15,118,110,0.12),rgba(190,24,93,0.12))]">
                    <feature.icon className="h-6 w-6 text-slate-800" />
                  </div>
                  <h3 className="mt-5 text-xl font-semibold text-slate-950">{feature.title}</h3>
                  <p className="mt-3 text-sm leading-7 text-slate-600">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="px-6 py-16">
          <div className="mx-auto max-w-4xl rounded-[36px] border border-[rgba(15,23,42,0.08)] bg-white p-10 text-center shadow-[0_28px_80px_rgba(15,23,42,0.07)]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
              Start Flowtrack
            </p>
            <h2 className="mt-4 font-serif text-4xl text-slate-950">
              Bring tickets, milestones, and releases into one workflow.
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg leading-8 text-slate-600">
              Use the same workspace for external issue reporting and internal delivery execution, with
              tenant-aware access controls and auditable workflow state.
            </p>
            <div className="mt-8 flex flex-col justify-center gap-4 sm:flex-row">
              <Link href="/login">
                <Button variant="outline" size="lg">
                  Sign in
                </Button>
              </Link>
              <Link href="/signup">
                <Button size="lg">Create Flowtrack account</Button>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-[rgba(15,23,42,0.08)] px-6 py-8">
        <div className="mx-auto max-w-7xl text-center text-sm text-slate-500">
          © {new Date().getFullYear()} Flowtrack. Ticketing and project delivery in one workspace.
        </div>
      </footer>
    </div>
  );
}
